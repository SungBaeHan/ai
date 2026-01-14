# ========================================
# apps/api/routes/characters.py — 캐릭터 API
# - GET /v1/characters           : 목록
# - GET /v1/characters/{id}      : 단일(숫자 또는 char_XX 모두 허용)
# - GET /v1/characters/count     : 총 개수
# - POST /v1/characters          : 생성(전체 필드)
# - POST /v1/characters/upload-image : 이미지 업로드
# - POST /v1/characters/ai-detail    : AI 상세 생성
# 서버에서 image 값을 항상 절대경로(/assets/...)로 정규화해서 내려줌
# ========================================

import time
import logging
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Query, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel, Field, ConfigDict, field_validator
from adapters.persistence.factory import get_character_repo
from adapters.persistence.mongo import get_db
from src.domain.character import Character
from apps.api.utils.common import build_public_image_url
from adapters.file_storage.r2_storage import R2Storage
from langchain_openai import ChatOpenAI
from apps.api.dependencies.auth import get_optional_user, User
from apps.api.core.user_info_token import decode_user_info_token
from adapters.persistence.mongo.factory import get_mongo_client
from apps.api.deps.auth import get_current_user_from_token
from bson import ObjectId
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

router = APIRouter()                                   # 서브 라우터
repo = get_character_repo()                            # Repository 인터페이스를 통한 접근

# R2 Storage 인스턴스 (지연 초기화)
_r2_storage: Optional[R2Storage] = None

def get_r2_storage() -> R2Storage:
    """R2 Storage 싱글톤 인스턴스 반환"""
    global _r2_storage
    if _r2_storage is None:
        try:
            _r2_storage = R2Storage()
        except Exception as e:
            logger.error(f"Failed to initialize R2Storage: {e}")
            raise HTTPException(status_code=500, detail="R2 storage not configured")
    return _r2_storage

# === 이미지 경로 정규화 ===
def normalize_image(path: str | None) -> str | None:
    """
    이미지 경로를 R2 public URL로 변환합니다.
    
    - 이미 전체 URL인 경우 그대로 반환
    - 파일명을 추출하여 /assets/char/ 접두사를 사용한 R2 public URL 생성
    """
    return build_public_image_url(path)

def normalize_image_path(image_url: Optional[str]) -> str:
    """
    R2 공개 URL을 내부 저장 경로('/assets/...')로 변환한다.
    
    - 예: 'https://pub-xxxx.r2.dev/assets/char/abcd.png'
      → '/assets/char/abcd.png'
    - 이미 '/assets/...' 형태면 그대로 반환
    """
    if not image_url:
        return ""
    
    # 이미 내부 경로 형태인 경우
    if image_url.startswith("/assets/"):
        return image_url
    
    parts = image_url.split("/")
    # "assets"가 있는 위치부터 끝까지 이어 붙여서 내부 경로로 사용
    try:
        idx = parts.index("assets")
        return "/" + "/".join(parts[idx:])
    except ValueError:
        # "assets"가 없으면 원본 그대로 반환 (방어 코드)
        return image_url

def get_next_character_id(db):
    """
    characters 컬렉션에서 가장 큰 id 값을 찾아 +1 해서 반환한다.
    
    - 문서가 없다면 1부터 시작한다.
    """
    # id 내림차순으로 하나만 가져오기
    # pymongo는 동기 함수이므로 await 없이 사용
    doc = db.characters.find_one({}, sort=[("id", -1)])
    if doc and "id" in doc:
        try:
            return int(doc["id"]) + 1
        except (TypeError, ValueError):
            # id가 이상한 값이어도 최소한 1부터 시작하도록
            pass
    return 1

class CharacterIn(BaseModel):
    """캐릭터 생성 입력 모델"""
    name: str = Field(..., description="캐릭터 이름")
    summary: str = Field(..., description="한 줄 소개")
    detail: str = Field("", description="상세 설명")
    tags: List[str] = Field(default_factory=lambda: ["TRPG", "캐릭터"])
    image: str = Field(..., description="이미지 경로 (/assets/char/xxx.png 등)")

@router.get("", summary="캐릭터 목록")
def get_list(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1), q: str = Query(None), db = Depends(get_db)):
    """캐릭터 목록 반환(서버가 image를 절대경로로 보정, created_at 기준 최신순 정렬)"""
    # MongoDB 어댑터에만 list_paginated가 있을 수 있으므로 getattr로 안전 호출
    fn = getattr(repo, "list_paginated", None)
    if callable(fn):
        try:
            result = fn(skip=skip, limit=limit, q=q)
            items = result.get("items", [])
            for it in items:
                it["image"] = normalize_image(it.get("image"))
                # creator ObjectId를 문자열로 변환
                if "creator" in it and it["creator"] is not None:
                    it["creator"] = str(it["creator"])
            return {
                "items": items,
                "total": result.get("total", len(items)),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            print(f"[WARN] Repository list_paginated failed: {e}. Falling back to direct MongoDB query.")
    
    # MongoDB 직접 쿼리 (created_at 기준 최신순 정렬)
    filter_query = {}
    if q:
        filter_query = {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
                {"summary": {"$regex": q, "$options": "i"}},
            ]
        }
    
    cursor = db.characters.find(filter_query).sort([
        ("created_at", -1),
        ("id", -1),
    ]).skip(skip).limit(limit)
    
    items = []
    for doc in cursor:
        doc.pop("_id", None)  # _id 제거
        doc["image"] = normalize_image(doc.get("image"))
        # creator ObjectId를 문자열로 변환
        if "creator" in doc and doc["creator"] is not None:
            doc["creator"] = str(doc["creator"])
        # 프론트엔드 호환성을 위해 summary를 shortBio로도 매핑
        if "summary" in doc and "shortBio" not in doc:
            doc["shortBio"] = doc["summary"]
        # detail을 longBio로도 매핑
        if "detail" in doc and "longBio" not in doc:
            doc["longBio"] = doc["detail"]
        items.append(doc)
    
    total = db.characters.count_documents(filter_query)
    return {"items": items, "total": total, "skip": skip, "limit": limit}

@router.get("/{character_id}", summary="캐릭터 단일 조회")
def get_one(character_id: str):
    """
    단일 캐릭터 조회
    - '6' 또는 'char_06' 모두 허용
    """
    cid = character_id
    if isinstance(cid, str) and cid.startswith("char_"):
        # 'char_06' → 6
        try:
            cid = int(cid.split("_", 1)[1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid character id")
    try:
        cid = int(cid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid character id")

    # Repository 인터페이스를 통한 조회
    char = repo.get_by_id(cid)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_dict = char.to_dict()
    char_dict["image"] = normalize_image(char_dict.get("image"))
    # creator는 이미 문자열로 변환되어 있음 (Character.to_dict에서)
    # 프론트엔드 호환성을 위해 summary를 shortBio로도 매핑
    if "summary" in char_dict and "shortBio" not in char_dict:
        char_dict["shortBio"] = char_dict["summary"]
    # detail을 longBio로도 매핑
    if "detail" in char_dict and "longBio" not in char_dict:
        char_dict["longBio"] = char_dict["detail"]
    return char_dict

@router.get("/count", summary="캐릭터 총 개수")
def get_count():
    """등록된 캐릭터 총 수 반환"""
    # Repository 인터페이스를 통한 조회
    return {"count": repo.count()}

@router.get("/my", summary="내가 만든 캐릭터 목록")
def get_my_characters(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    q: str = Query(None),
    db = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    현재 로그인한 사용자가 만든 캐릭터 목록 조회
    - creator == current_user._id 조건으로 필터링
    - 로그인 필수
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    # user_id를 ObjectId로 변환
    user_id_str = current_user.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
    
    try:
        creator_id = ObjectId(user_id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")
    
    # 필터 쿼리 구성
    filter_query = {"creator": creator_id}
    
    # 검색어가 있으면 추가 필터
    if q:
        filter_query["$and"] = [
            {"creator": creator_id},
            {
                "$or": [
                    {"name": {"$regex": q, "$options": "i"}},
                    {"tags": {"$regex": q, "$options": "i"}},
                    {"summary": {"$regex": q, "$options": "i"}},
                ]
            }
        ]
    
    # MongoDB 쿼리
    cursor = db.characters.find(filter_query).sort([
        ("created_at", -1),
        ("id", -1),
    ]).skip(skip).limit(limit)
    
    items = []
    for doc in cursor:
        doc.pop("_id", None)  # _id 제거
        doc["image"] = normalize_image(doc.get("image"))
        # creator ObjectId를 문자열로 변환
        if "creator" in doc and doc["creator"] is not None:
            doc["creator"] = str(doc["creator"])
        # 프론트엔드 호환성을 위해 summary를 shortBio로도 매핑
        if "summary" in doc and "shortBio" not in doc:
            doc["shortBio"] = doc["summary"]
        # detail을 longBio로도 매핑
        if "detail" in doc and "longBio" not in doc:
            doc["longBio"] = doc["detail"]
        items.append(doc)
    
    total = db.characters.count_documents(filter_query)
    return {"items": items, "total": total, "skip": skip, "limit": limit}

# === 이미지 업로드 ===
@router.post("/upload-image", summary="캐릭터 이미지 업로드")
async def upload_character_image(file: UploadFile = File(...)):
    """
    캐릭터 생성 화면에서 대표 이미지를 업로드하면 R2에 저장하고 URL과 메타를 반환
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Content-Type 확인
        content_type = file.content_type or "image/png"
        if not content_type.startswith("image/"):
            content_type = "image/png"
        
        # R2에 업로드
        r2 = get_r2_storage()
        meta = r2.upload_image(content, prefix="assets/char/", content_type=content_type)
        
        return {
            "image": meta["url"],
            "src_file": meta["src_file"],
            "img_hash": meta["img_hash"],
            "key": meta["key"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# === AI 상세 생성 ===
class CharacterBaseInfo(BaseModel):
    """캐릭터 기본 정보 (AI 생성용)"""
    name: Optional[str] = None
    archetype: Optional[str] = None
    world: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class CharacterExample(BaseModel):
    """예시 대화 모델"""
    user: str
    assistant: str

class CharacterDetailResponse(BaseModel):
    """AI 생성된 캐릭터 상세 정보"""
    background: str
    detail: str
    greeting: str
    style: str
    persona_traits: List[str]
    examples: List[Dict[str, str]]
    scenario: str
    system_prompt: str
    # 왼쪽 폼용 추천 값
    suggested_name: Optional[str] = None
    suggested_archetype: Optional[str] = None
    suggested_world: Optional[str] = None
    suggested_summary: Optional[str] = None
    suggested_tags: List[str] = Field(default_factory=list)

class CharacterMeta(BaseModel):
    """캐릭터 생성 메타데이터 모델"""
    model_config = ConfigDict(extra='ignore')
    
    id: Optional[int] = None
    name: str
    archetype: Optional[str] = None
    world: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    background: Optional[str] = None
    detail: Optional[str] = None
    greeting: Optional[str] = None
    style: Optional[str] = None
    persona_traits: List[str] = Field(default_factory=list)
    examples: List[CharacterExample] = Field(default_factory=list)
    scenario: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[str] = "active"
    image: Optional[str] = None
    image_path: Optional[str] = None
    src_file: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    reg_user: Optional[str] = Field(default=None, description="등록한 사용자의 google_id 또는 email")
    gender: Optional[Literal["male", "female", "none"]] = Field(default="none", description="성별: male/female/none")
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """gender 값 검증"""
        if v is None:
            return "none"
        if v not in ["male", "female", "none"]:
            raise ValueError("gender must be one of: male, female, none")
        return v

@router.post("/ai-detail", response_model=CharacterDetailResponse, summary="AI로 캐릭터 상세 생성")
async def ai_generate_character_detail(payload: CharacterBaseInfo):
    """
    캐릭터 기본 정보를 바탕으로 상세 설정을 AI가 생성합니다.
    이름이 없어도 AI가 추천 이름을 생성합니다.
    """
    try:
        # 프롬프트 구성
        tags_str = ", ".join(payload.tags) if payload.tags else "없음"
        has_name = bool(payload.name and payload.name.strip())
        has_archetype = bool(payload.archetype and payload.archetype.strip())
        has_world = bool(payload.world and payload.world.strip())
        has_summary = bool(payload.summary and payload.summary.strip())
        has_tags = len(payload.tags) > 0
        
        # 표시용 이름 (없으면 "이 캐릭터" 사용)
        display_name = payload.name.strip() if has_name else "이 캐릭터"
        
        # suggested_* 필드 JSON 스키마 생성
        suggested_fields = []
        if not has_name:
            suggested_fields.append('  "suggested_name": "적절한 캐릭터 이름"')
        if not has_archetype:
            suggested_fields.append('  "suggested_archetype": "적절한 아키타입/직업"')
        if not has_world:
            suggested_fields.append('  "suggested_world": "적절한 세계관 이름"')
        if not has_summary:
            suggested_fields.append('  "suggested_summary": "한 줄 요약"')
        if not has_tags:
            suggested_fields.append('  "suggested_tags": ["태그1", "태그2"]')
        
        suggested_fields_str = ",\n".join(suggested_fields) if suggested_fields else ""
        comma_before_suggested = ",\n" if suggested_fields_str else ""
        
        prompt = f"""다음 정보를 바탕으로 TRPG 캐릭터의 상세 설정을 생성해주세요.

캐릭터 이름: {display_name}
아키타입/직업: {payload.archetype or "미정"}
소속 세계관: {payload.world or "미정"}
한 줄 요약: {payload.summary or "없음"}
태그: {tags_str}

다음 JSON 형식으로 응답해주세요:
{{
  "background": "캐릭터의 배경 스토리와 과거 (3-5문장)",
  "detail": "성격과 특징에 대한 상세 설명 (3-5문장)",
  "greeting": "첫 만남 시 인사말 (1문장, 구어체)",
  "style": "말투와 톤 설명 (예: 시크하고 간결한 톤, 현장 보고체)",
  "persona_traits": ["특징1", "특징2", "특징3"],
  "examples": [
    {{"user": "사용자 대사 예시", "assistant": "캐릭터 응답 예시"}},
    {{"user": "사용자 대사 예시2", "assistant": "캐릭터 응답 예시2"}}
  ],
  "scenario": "TRPG 시작 장면 설명 (2-3문장)",
  "system_prompt": "캐릭터의 행동과 말투를 지시하는 시스템 프롬프트 (2-3문장)"{comma_before_suggested}
{suggested_fields_str}
}}

중요:
- 이미 입력된 값(name, archetype, world, summary, tags)이 있으면 해당 suggested_* 필드는 null 또는 빈 문자열로 설정하세요.
- 비어있는 필드에 대해서만 suggested_* 값을 제안해주세요.
- 반드시 유효한 JSON만 반환하고, 다른 설명은 포함하지 마세요."""
        
        # OpenAI 호출
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates TRPG character details in JSON format. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.invoke(messages)
        content = getattr(response, "content", str(response))
        
        # JSON 파싱
        try:
            # JSON 코드 블록 제거 (```json ... ```)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {content[:200]}")
            # 기본값 반환
            data = {
                "background": f"{payload.name}의 배경 스토리입니다.",
                "detail": f"{payload.name}의 성격과 특징입니다.",
                "greeting": "안녕하세요.",
                "style": "자연스러운 구어체",
                "persona_traits": ["친절함", "책임감"],
                "examples": [
                    {"user": "안녕", "assistant": "안녕하세요."}
                ],
                "scenario": "모험이 시작됩니다.",
                "system_prompt": f"{payload.name}의 행동과 말투를 유지하세요."
            }
        
        return CharacterDetailResponse(
            background=data.get("background", ""),
            detail=data.get("detail", ""),
            greeting=data.get("greeting", ""),
            style=data.get("style", ""),
            persona_traits=data.get("persona_traits", []),
            examples=data.get("examples", []),
            scenario=data.get("scenario", ""),
            system_prompt=data.get("system_prompt", ""),
            suggested_name=data.get("suggested_name") if not has_name else None,
            suggested_archetype=data.get("suggested_archetype") if not has_archetype else None,
            suggested_world=data.get("suggested_world") if not has_world else None,
            suggested_summary=data.get("suggested_summary") if not has_summary else None,
            suggested_tags=data.get("suggested_tags", []) if not has_tags else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("AI generation failed")
        raise HTTPException(status_code=500, detail="캐릭터 상세 설정 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

# === 사용자 인증 의존성은 worlds.py에서 import ===
# 인증 함수는 apps.api.deps.auth.get_current_user_from_token을 사용

@router.post("", summary="캐릭터 생성")
async def create_character(
    file: UploadFile = File(...),
    meta: str = Form(...),
    db = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    캐릭터 이미지와 메타데이터를 함께 받아 R2 업로드 + Mongo 저장.
    - file: 캐릭터 이미지 파일
    - meta: JSON 문자열 (CharacterMeta 구조)
    - 로그인 필수, is_use/is_lock 정책 적용
    """
    try:
        # --- 로그인 및 사용 가능 여부 체크 ---
        
        if current_user is None:
            # dependency가 None을 반환하는 형태라면 여기서 401
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        # 필드 이름: users 컬렉션 구조에 맞게
        # 예: isUse / isLock 을 쓰는 경우가 많음
        is_use = current_user.get("is_use") or current_user.get("isUse")
        is_lock = current_user.get("is_lock") or current_user.get("isLock")
        
        # 사용 불가
        if is_use is not None and is_use != "Y":
            raise HTTPException(status_code=403, detail="현재 사용이 불가한 상태입니다.")
        
        # 계정 잠금
        if is_lock is not None and is_lock == "Y":
            raise HTTPException(status_code=403, detail="현재 계정이 차단된 상태입니다.")
        
        # 1) meta 파싱
        try:
            payload = CharacterMeta.model_validate_json(meta)
        except Exception as e:
            logger.error(f"Failed to parse meta JSON: {e}")
            raise HTTPException(status_code=400, detail="캐릭터 정보(meta)가 올바르지 않습니다.")
        
        if not payload.name or not payload.name.strip():
            raise HTTPException(status_code=400, detail="캐릭터 이름을 입력해주세요.")
        
        # 2) 이미지 읽기
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="대표 이미지 파일이 전송되지 않았습니다.")
        
        # 3) Content-Type 확인
        content_type = file.content_type or "image/png"
        if not content_type.startswith("image/"):
            content_type = "image/png"
        
        # 4) R2 업로드
        try:
            r2 = get_r2_storage()
            image_meta = r2.upload_image(content, prefix="assets/char/", content_type=content_type)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"[R2_UPLOAD_ERROR] {e}")
            raise HTTPException(status_code=502, detail="이미지 업로드 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
        
        # 5) MongoDB 저장
        try:
            from fastapi.encoders import jsonable_encoder
            import hashlib
            
            # 1) id 자동 증가: 가장 큰 id + 1
            new_id = get_next_character_id(db)
            
            # 2) image URL → 내부 경로('/assets/...')로 정규화
            normalized_path = normalize_image_path(image_meta["url"])
            
            # 3) 타임스탬프 설정 (초 단위 UNIX time)
            now = int(time.time())
            
            # --- 등록자(reg_user) 정보 세팅 ---
            # google_id 우선, 없으면 email
            google_id = (
                current_user.get("google_id")
                or current_user.get("googleId")
                or current_user.get("sub")
            )
            email = current_user.get("email")
            if google_id:
                reg_user = str(google_id)
            elif email:
                reg_user = email
            else:
                reg_user = None
            
            # 예시 대화를 Dict 형태로 변환
            examples_dict = [
                {"user": ex.user, "assistant": ex.assistant}
                for ex in payload.examples
            ]
            
            # gender 필드 처리: 없으면 "none" 기본값
            gender_value = payload.gender if payload.gender else "none"
            
            # --- creator 필드 세팅 (보안: payload의 creator는 무시, 서버에서만 설정) ---
            creator_id = None
            user_id_str = current_user.get("user_id")
            if user_id_str:
                try:
                    # user_id를 ObjectId로 변환하여 저장
                    creator_id = ObjectId(user_id_str)
                except Exception:
                    logger.warning(f"Invalid user_id format: {user_id_str}")
                    creator_id = None
            
            doc = {
                "id": new_id,
                "name": payload.name.strip(),
                "archetype": payload.archetype,
                "world": payload.world,
                "summary": payload.summary or "",
                "tags": payload.tags or [],
                "image": normalized_path,  # 내부 경로로 저장
                "image_path": normalized_path,  # 내부 경로로 저장
                "src_file": normalized_path,  # 내부 경로로 저장
                "image_hash": hashlib.md5(content).hexdigest(),
                "background": payload.background,
                "detail": payload.detail or "",
                "greeting": payload.greeting,
                "style": payload.style,
                "persona_traits": payload.persona_traits or [],
                "examples": examples_dict,
                "scenario": payload.scenario or "",
                "system_prompt": payload.system_prompt or "",
                "status": payload.status or "active",
                "gender": gender_value,  # 성별 필드
                "creator": creator_id,  # 생성자 사용자 ID (ObjectId)
                "reg_user": reg_user,  # 등록자 식별자
                "created_at": now,
                "updated_at": now,
                # 기존 캐릭터 문서에 쓰던 필드 기본값들
                "polish_model": "gpt-4o-mini",
                "polish_status": "done",
                "vision_model": "moondream",
                "meta_version": 2,
            }
            
            result = db.characters.insert_one(doc)
            inserted_id = str(result.inserted_id)
            
            # 응답용으로 ObjectId를 문자열로 변환
            resp = {
                "id": new_id,
                "mongo_id": inserted_id,
                "status": "ok",
            }
            
            return jsonable_encoder(resp)
        except Exception as e:
            logger.exception(f"[MONGO_INSERT_ERROR] {e}")
            raise HTTPException(status_code=500, detail="캐릭터 정보를 저장하는 중 서버 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
            logger.exception("Character creation failed")
            raise HTTPException(status_code=500, detail="캐릭터 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")


@router.get("/{character_id}/chat/bootstrap", summary="캐릭터 채팅 재개 (Bootstrap)")
async def bootstrap_character_chat(
    character_id: str,
    limit: int = Query(50, ge=1, le=200, description="최대 메시지 수"),
    request: Request = None,
    db = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    캐릭터 채팅 세션을 불러와서 재개합니다.
    - (user_id, character_id) 기준으로 세션을 조회
    - 해당 세션의 메시지 히스토리를 created_at 오름차순으로 반환
    - 세션이 없으면 빈 세션과 빈 메시지 목록 반환
    """
    try:
        if current_user is None:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        user_id = current_user.get("google_id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
        
        # character_id 정규화 (char_XX 형태 처리)
        char_id_str = character_id
        if isinstance(char_id_str, str) and char_id_str.startswith("char_"):
            try:
                char_id_str = str(int(char_id_str.split("_", 1)[1]))
            except Exception:
                pass
        else:
            char_id_str = str(char_id_str)
        
        # 1) 세션 조회 (get-or-create)
        session_col = db["characters_session"]
        session_filter = {
            "user_id": str(user_id),
            "chat_type": "character",
            "entity_id": char_id_str,
        }
        
        session_doc = session_col.find_one(session_filter)
        
        if not session_doc:
            # 세션이 없으면 빈 세션 정보 반환
            return {
                "session": None,
                "messages": [],
            }
        
        session_id = session_doc["_id"]
        
        # 2) 메시지 조회 (created_at 오름차순)
        message_col = db["characters_message"]
        cursor = message_col.find(
            {"session_id": session_id}
        ).sort("created_at", 1).limit(limit)
        
        messages = []
        for msg_doc in cursor:
            msg = {
                "id": str(msg_doc["_id"]),
                "session_id": str(msg_doc.get("session_id", "")),
                "role": msg_doc.get("role", "user"),
                "content": msg_doc.get("content", ""),
                "created_at": msg_doc.get("created_at"),
            }
            if "request_id" in msg_doc:
                msg["request_id"] = msg_doc["request_id"]
            if "meta" in msg_doc:
                msg["meta"] = msg_doc["meta"]
            messages.append(msg)
        
        # 3) 세션 정보 정리 (ObjectId를 문자열로 변환)
        session_summary = {
            "id": str(session_doc["_id"]),
            "user_id": session_doc.get("user_id"),
            "chat_type": session_doc.get("chat_type"),
            "entity_id": session_doc.get("entity_id"),
            "status": session_doc.get("status", "idle"),
            "created_at": session_doc.get("created_at"),
            "updated_at": session_doc.get("updated_at"),
            "last_message_at": session_doc.get("last_message_at"),
            "last_message_preview": session_doc.get("last_message_preview"),
            "state_version": session_doc.get("state_version", 0),
        }
        
        # persona 필드가 있으면 포함
        if "persona" in session_doc:
            session_summary["persona"] = session_doc.get("persona")
        
        logger.info(
            "[CHAT][BOOTSTRAP] user=%s char=%s session_id=%s messages_count=%d",
            user_id,
            char_id_str,
            session_summary["id"],
            len(messages),
        )
        
        return {
            "session": session_summary,
            "messages": messages,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[CHAT][BOOTSTRAP][ERROR] character_id=%s error=%s", character_id, str(e))
        raise HTTPException(status_code=500, detail=f"채팅 재개 중 오류가 발생했습니다: {str(e)}")