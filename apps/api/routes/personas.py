from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
import random
import string

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, field_validator

from adapters.file_storage.r2_storage import R2Storage
from adapters.persistence.mongo.factory import get_mongo_client
from adapters.persistence.mongo import get_db
from apps.api.routes.worlds import get_current_user_v2
from apps.api.utils.common import build_public_image_url


router = APIRouter(tags=["personas"])

# ================================
# 공통 상수 / 헬퍼
# ================================

PERSONA_PRESETS: List[Dict[str, str]] = [
    # 기본 16개 프리셋 (F01-F08: 여성, M01-M08: 남성)
    {"preset_key": "F01", "gender": "female", "url": "/assets/persona/F01.png"},
    {"preset_key": "F02", "gender": "female", "url": "/assets/persona/F02.png"},
    {"preset_key": "F03", "gender": "female", "url": "/assets/persona/F03.png"},
    {"preset_key": "F04", "gender": "female", "url": "/assets/persona/F04.png"},
    {"preset_key": "F05", "gender": "female", "url": "/assets/persona/F05.png"},
    {"preset_key": "F06", "gender": "female", "url": "/assets/persona/F06.png"},
    {"preset_key": "F07", "gender": "female", "url": "/assets/persona/F07.png"},
    {"preset_key": "F08", "gender": "female", "url": "/assets/persona/F08.png"},
    {"preset_key": "M01", "gender": "male", "url": "/assets/persona/M01.png"},
    {"preset_key": "M02", "gender": "male", "url": "/assets/persona/M02.png"},
    {"preset_key": "M03", "gender": "male", "url": "/assets/persona/M03.png"},
    {"preset_key": "M04", "gender": "male", "url": "/assets/persona/M04.png"},
    {"preset_key": "M05", "gender": "male", "url": "/assets/persona/M05.png"},
    {"preset_key": "M06", "gender": "male", "url": "/assets/persona/M06.png"},
    {"preset_key": "M07", "gender": "male", "url": "/assets/persona/M07.png"},
    {"preset_key": "M08", "gender": "male", "url": "/assets/persona/M08.png"},
]

MAX_PERSONAS = 5
VALID_PRESET_KEYS = [f"F{i:02d}" for i in range(1, 9)] + [f"M{i:02d}" for i in range(1, 9)]


class PersonaBase(BaseModel):
    """공통 필드"""

    name: str = Field(..., min_length=1, max_length=25, description="페르소나 이름/호칭")
    gender: Literal["male", "female", "nonbinary"] = "nonbinary"
    bio: str = Field("", max_length=700, description="소개 텍스트")
    image_key: str = Field(..., description="프리셋 이미지 키 (F01~F08: 여성, M01~M08: 남성)")
    is_default: bool = False

    @field_validator("image_key")
    @classmethod
    def validate_image_key(cls, v: str) -> str:
        if v not in VALID_PRESET_KEYS:
            raise ValueError(f"image_key는 {VALID_PRESET_KEYS[0]} ~ {VALID_PRESET_KEYS[-1]} 중 하나여야 합니다.")
        return v


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    """부분 수정용"""

    name: Optional[str] = Field(None, min_length=1, max_length=25)
    gender: Optional[Literal["male", "female", "nonbinary"]] = None
    bio: Optional[str] = Field(None, max_length=700)
    image_key: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("image_key")
    @classmethod
    def validate_image_key(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRESET_KEYS:
            raise ValueError(f"image_key는 {VALID_PRESET_KEYS[0]} ~ {VALID_PRESET_KEYS[-1]} 중 하나여야 합니다.")
        return v


class PersonaOut(PersonaBase):
    persona_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PersonaPresetOut(BaseModel):
    preset_key: str
    gender: Literal["male", "female", "nonbinary"]
    url: str


def _get_users_collection():
    db = get_mongo_client()
    return db.users


def get_default_persona(user_id: str) -> Optional[Dict[str, Any]]:
    """
    사용자의 기본 페르소나를 반환한다.
    - user_id: 사용자 ObjectId 문자열
    - 반환: persona dict 또는 None
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    
    users = _get_users_collection()
    user_doc = users.find_one({"_id": oid})
    if not user_doc:
        return None
    
    personas = _ensure_personas_array(user_doc)
    for p in personas:
        if p.get("is_default"):
            return p
    
    return None


def _ensure_personas_array(user_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    personas = user_doc.get("personas")
    if not isinstance(personas, list):
        personas = []
        user_doc["personas"] = personas
    return personas


def _generate_persona_id() -> str:
    """SDD 스펙: p_<yyyymmdd>_<rand4> 형식으로 persona_id 생성"""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    rand4 = ''.join(random.choices(string.digits, k=4))
    return f"p_{date_str}_{rand4}"


def _normalize_persona_doc(doc: Dict[str, Any]) -> PersonaOut:
    # 기존 image 필드가 있으면 image_key로 변환 (마이그레이션)
    image_key = doc.get("image_key")
    if not image_key and "image" in doc:
        image_obj = doc.get("image", {})
        if isinstance(image_obj, dict):
            old_key = image_obj.get("preset_key")
            # 기존 preset_XX 형식을 F01/M01 형식으로 변환 (간단한 매핑)
            if old_key and old_key.startswith("preset_"):
                try:
                    num = int(old_key.replace("preset_", ""))
                    # 기존 매핑: preset_01-04=male, preset_05-08=female, preset_09-10=male, preset_11-12=female, preset_13=male, preset_14=female, preset_15=male, preset_16=female
                    # 새 매핑: F01-F08=female, M01-M08=male
                    if num <= 4 or num == 9 or num == 10 or num == 13 or num == 15:
                        image_key = f"M{((num - 1) % 8) + 1:02d}"
                    else:
                        image_key = f"F{((num - 1) % 8) + 1:02d}"
                except:
                    image_key = "F01"
            else:
                image_key = old_key or "F01"
    if not image_key or image_key not in VALID_PRESET_KEYS:
        image_key = "F01"
    
    return PersonaOut(
        persona_id=doc["persona_id"],
        name=doc.get("name", ""),
        gender=doc.get("gender", "nonbinary"),
        bio=doc.get("bio") or doc.get("intro", ""),  # intro → bio 마이그레이션
        image_key=image_key,
        is_default=bool(doc.get("is_default", False)),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


# ================================
# Preset 목록
# ================================


@router.get("/personas/presets", response_model=List[PersonaPresetOut])
def list_persona_presets() -> List[PersonaPresetOut]:
    """
    기본 16개 페르소나 프리셋 목록을 반환한다.
    """
    presets: List[PersonaPresetOut] = []
    for item in PERSONA_PRESETS:
        gender = item.get("gender", "nonbinary")
        if gender not in ("male", "female", "nonbinary"):
            gender = "nonbinary"
        presets.append(
            PersonaPresetOut(
                preset_key=item["preset_key"],
                gender=gender,  # type: ignore[arg-type]
                url=item["url"],
            )
        )
    return presets


# ================================
# 내 페르소나 CRUD
# ================================


@router.get("/users/me/personas", response_model=List[PersonaOut])
def get_my_personas(current_user=Depends(get_current_user_v2)) -> List[PersonaOut]:
    """
    로그인한 사용자의 personas 배열을 반환한다.
    기본 페르소나는 is_default=true 로 표시되며, 항상 맨 앞에 오도록 정렬한다.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    users = _get_users_collection()
    try:
        oid = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")

    user_doc = users.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    personas = _ensure_personas_array(user_doc)
    # default 먼저, 그 다음 최신순(created_at desc)
    def sort_key(p: Dict[str, Any]):
        return (
            0 if p.get("is_default") else 1,
            -(p.get("created_at") or datetime.fromtimestamp(0, tz=timezone.utc)).timestamp(),
        )

    personas_sorted = sorted(personas, key=sort_key)
    return [_normalize_persona_doc(p) for p in personas_sorted]


@router.post("/users/me/personas", response_model=PersonaOut)
def create_persona(
    payload: PersonaCreate,
    current_user=Depends(get_current_user_v2),
) -> PersonaOut:
    """
    새 페르소나를 생성한다.
    - persona_id 규칙: p_<yyyymmdd>_<rand4>
    - 최대 5개까지 생성 가능
    - 첫 페르소나는 자동으로 is_default=true
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    users = _get_users_collection()
    try:
        oid = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")

    user_doc = users.find_one({"_id": oid}) or {"_id": oid}
    personas = _ensure_personas_array(user_doc)

    # 최대 5개 제한 검증
    if len(personas) >= MAX_PERSONAS:
        raise HTTPException(
            status_code=409,
            detail=f"최대 {MAX_PERSONAS}개까지 생성 가능합니다."
        )

    now = datetime.now(timezone.utc)
    # persona_id 유니크 보장 (충돌 시 재생성)
    persona_id = _generate_persona_id()
    max_retries = 10
    for _ in range(max_retries):
        if not any(p.get("persona_id") == persona_id for p in personas):
            break
        persona_id = _generate_persona_id()
    else:
        raise HTTPException(status_code=500, detail="persona_id 생성 실패")

    # 기본 페르소나 여부 결정
    is_default = bool(payload.is_default)
    if not personas:
        # 첫 페르소나는 무조건 기본
        is_default = True

    if is_default:
        for p in personas:
            p["is_default"] = False

    new_doc: Dict[str, Any] = {
        "persona_id": persona_id,
        "name": payload.name,
        "gender": payload.gender,
        "bio": payload.bio,
        "image_key": payload.image_key,
        "is_default": is_default,
        "created_at": now,
        "updated_at": now,
    }
    personas.append(new_doc)

    users.update_one(
        {"_id": oid},
        {"$set": {"personas": personas}},
        upsert=True,
    )

    return _normalize_persona_doc(new_doc)


@router.put("/users/me/personas/{persona_id}", response_model=PersonaOut)
def update_persona(
    persona_id: str,
    payload: PersonaUpdate,
    current_user=Depends(get_current_user_v2),
) -> PersonaOut:
    """
    기존 페르소나 수정.
    - name/gender/bio/image_key/is_default 중 일부만 수정 가능
    - is_default=true 로 변경 시 다른 페르소나는 false 처리
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    users = _get_users_collection()
    try:
        oid = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")

    user_doc = users.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    personas = _ensure_personas_array(user_doc)
    target = next((p for p in personas if p.get("persona_id") == persona_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")

    data = payload.model_dump(exclude_unset=True)

    # default 변경 여부
    want_default = data.get("is_default")
    if want_default is True:
        for p in personas:
            p["is_default"] = False
        target["is_default"] = True
    elif want_default is False:
        # 명시적으로 false 로 바꾸면 그대로 반영
        target["is_default"] = False

    if "name" in data:
        target["name"] = data["name"]
    if "gender" in data:
        target["gender"] = data["gender"]
    if "bio" in data:
        target["bio"] = data["bio"]
    if "image_key" in data:
        target["image_key"] = data["image_key"]

    target["updated_at"] = datetime.now(timezone.utc)

    users.update_one({"_id": oid}, {"$set": {"personas": personas}})
    return _normalize_persona_doc(target)


@router.delete("/users/me/personas/{persona_id}")
def delete_persona(
    persona_id: str,
    current_user=Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    페르소나 삭제.
    - 삭제 대상이 기본 페르소나였다면: default가 "없어지는" 상태 허용(0개)
    - v1에서는 자동 지정 안 함
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    users = _get_users_collection()
    try:
        oid = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")

    user_doc = users.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    personas = _ensure_personas_array(user_doc)
    if not personas:
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")

    idx = next((i for i, p in enumerate(personas) if p.get("persona_id") == persona_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")

    personas.pop(idx)

    users.update_one({"_id": oid}, {"$set": {"personas": personas}})
    return {"ok": True, "deleted": True}


@router.patch("/users/me/personas/{persona_id}/default")
def set_default_persona(
    persona_id: str,
    current_user=Depends(get_current_user_v2),
) -> Dict[str, Any]:
    """
    기본 페르소나 지정 (PATCH 엔드포인트).
    - true만 받는 걸로 단순화(해제는 PUT에서만)
    - 기존 default false 처리 후 target true
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    users = _get_users_collection()
    try:
        oid = ObjectId(current_user["user_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")

    user_doc = users.find_one({"_id": oid})
    if not user_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    personas = _ensure_personas_array(user_doc)
    target = next((p for p in personas if p.get("persona_id") == persona_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")

    # 기존 default false 처리 후 target true
    for p in personas:
        p["is_default"] = False
    target["is_default"] = True
    target["updated_at"] = datetime.now(timezone.utc)

    users.update_one({"_id": oid}, {"$set": {"personas": personas}})
    return {"ok": True}


# ================================
# 업로드 API (R2)
# ================================

_r2_storage: Optional[R2Storage] = None


def get_r2_storage() -> R2Storage:
    global _r2_storage
    if _r2_storage is None:
        _r2_storage = R2Storage()
    return _r2_storage


class PersonaUploadResponse(BaseModel):
    url: str


@router.post("/uploads/persona-image", response_model=PersonaUploadResponse)
async def upload_persona_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user_v2),
) -> PersonaUploadResponse:
    """
    페르소나용 프로필 이미지를 업로드하고 R2 public URL을 반환한다.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    content_type = file.content_type or "image/png"
    if not content_type.startswith("image/"):
        content_type = "image/png"

    try:
        r2 = get_r2_storage()
        meta = r2.upload_image(content, prefix="assets/persona/", content_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    # build_public_image_url 로 절대 URL 변환
    public_url = build_public_image_url(meta.get("url") or meta.get("path"), prefix="persona")
    return PersonaUploadResponse(url=public_url)



