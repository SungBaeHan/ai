# ========================================
# apps/api/routes/worlds.py — 세계관 API
# - POST /v1/worlds/upload-image : 이미지 업로드
# - POST /v1/worlds/ai-detail    : AI 상세 생성
# - POST /v1/worlds              : 세계관 생성
# ========================================

import time
import logging
import hashlib
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request, Query
from pydantic import BaseModel, Field, ConfigDict
from adapters.persistence.mongo import get_db
from adapters.file_storage.r2_storage import R2Storage
from langchain_openai import ChatOpenAI
from apps.api.core.user_info_token import decode_user_info_token
from adapters.persistence.mongo.factory import get_mongo_client
from apps.api.utils.common import build_public_image_url
from apps.api.deps.auth import get_current_user_from_token
from bson import ObjectId
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
import json
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter()                                   # 서브 라우터


@router.get("/{world_id}/chat/bootstrap", summary="세계관 채팅 재개 (Bootstrap)")
async def bootstrap_world_chat(
    world_id: str,
    limit: int = Query(50, ge=1, le=200, description="최대 메시지 수"),
    request: Request = None,
    db = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    세계관 채팅 세션을 불러와서 재개합니다.
    - (user_id, world_id) 기준으로 세션을 조회
    - 해당 세션의 메시지 히스토리를 created_at 오름차순으로 반환
    - 세션이 없으면 빈 세션과 빈 메시지 목록 반환
    """
    try:
        if current_user is None:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        user_id = current_user.get("google_id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
        
        # world_id 정규화 (ObjectId 문자열 처리)
        world_id_str = str(world_id)
        
        # 1) 세션 조회 (get-or-create)
        session_col = db["worlds_session"]
        session_filter = {
            "user_id": str(user_id),
            "chat_type": "world",
            "entity_id": world_id_str,
        }
        
        logger.info(
            "[CHAT][BOOTSTRAP] world session filter: user_id=%s world_id=%s entity_id=%s",
            str(user_id),
            world_id_str,
            world_id_str,
        )
        
        session_doc = session_col.find_one(session_filter)
        
        if not session_doc:
            # 세션이 없으면 빈 세션 정보 반환
            logger.info("[CHAT][BOOTSTRAP] world session not found for user_id=%s world_id=%s", str(user_id), world_id_str)
            return {
                "session": None,
                "messages": [],
            }
        
        session_id = session_doc["_id"]
        
        # 2) 메시지 조회 (created_at 오름차순)
        # messages는 session_id로만 조회 (world_id/entity_id/chat_type 필드 없음)
        message_col = db["worlds_message"]
        message_filter = {"session_id": session_id}
        
        logger.info(
            "[CHAT][BOOTSTRAP] world message filter: session_id=%s",
            str(session_id),
        )
        
        cursor = message_col.find(message_filter).sort("created_at", 1).limit(limit)
        
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
            "persona": session_doc.get("persona"),
        }
        
        logger.info(
            "[CHAT][BOOTSTRAP] user=%s world=%s session_id=%s messages_count=%d",
            user_id,
            world_id_str,
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
        logger.exception("[CHAT][BOOTSTRAP][ERROR] world_id=%s error=%s", world_id, str(e))
        raise HTTPException(status_code=500, detail=f"채팅 재개 중 오류가 발생했습니다: {str(e)}")


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

def normalize_world_image(path: str | None) -> str | None:
    """
    이미지 경로를 R2 public URL로 변환합니다.
    
    - 이미 전체 URL인 경우 그대로 반환
    - 파일명을 추출하여 /assets/world/ 접두사를 사용한 R2 public URL 생성
    """
    return build_public_image_url(path, prefix="world")

# === 세계관 목록 ===
# [임시 주석 처리] 기존 구현 버전 - 나중에 stub을 실제 구현으로 교체할 때 참고용
# @router.get("", summary="세계관 목록")
# def get_worlds_list(
#     offset: int = Query(0, ge=0, alias="offset"),
#     limit: int = Query(20, ge=1, le=200, alias="limit"),
#     q: Optional[str] = Query(None, alias="q"),
#     db = Depends(get_db)
# ):
#     """
#     세계관 목록 반환 (created_at 기준 최신순 정렬)
#     - offset: 건너뛸 개수
#     - limit: 가져올 개수
#     - q: 검색어 (이름, 요약, 태그에서 검색)
#     """
#     try:
#         # 검색 쿼리 구성
#         filter_query = {}
#         if q:
#             filter_query = {
#                 "$or": [
#                     {"name": {"$regex": q, "$options": "i"}},
#                     {"tags": {"$regex": q, "$options": "i"}},
#                     {"summary": {"$regex": q, "$options": "i"}},
#                 ]
#             }
#         
#         # MongoDB에서 세계관 목록 조회 (created_at 기준 최신순)
#         cursor = db.worlds.find(filter_query).sort([("created_at", -1)]).skip(offset).limit(limit)
#         items = list(cursor)
#         
#         # 이미지 경로 정규화
#         for item in items:
#             if "image" in item:
#                 item["image"] = normalize_world_image(item.get("image"))
#             # ObjectId를 문자열로 변환
#             if "_id" in item:
#                 item["_id"] = str(item["_id"])
#         
#         # 전체 개수 조회
#         total = db.worlds.count_documents(filter_query)
#         
#         return {
#             "items": items,
#             "total": total,
#             "offset": offset,
#             "limit": limit
#         }
#     except Exception as e:
#         logger.exception("Failed to get worlds list")
#         raise HTTPException(status_code=500, detail=f"Failed to get worlds list: {str(e)}")

def normalize_image_path(image_url: Optional[str]) -> str:
    """
    R2 공개 URL을 내부 저장 경로('/assets/...')로 변환한다.
    
    - 예: 'https://img.arcanaverse.ai/assets/world/abcd.png'
      → '/assets/world/abcd.png'
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

def get_next_world_id(db):
    """
    worlds 컬렉션에서 가장 큰 id 값을 찾아 +1 해서 반환한다.
    
    - 문서가 없다면 1부터 시작한다.
    """
    # id 내림차순으로 하나만 가져오기
    # pymongo는 동기 함수이므로 await 없이 사용
    doc = db.worlds.find_one({}, sort=[("id", -1)])
    if doc and "id" in doc:
        try:
            return int(doc["id"]) + 1
        except (TypeError, ValueError):
            # id가 이상한 값이어도 최소한 1부터 시작하도록
            pass
    return 1

# 인증 함수는 apps.api.deps.auth.get_current_user_from_token을 직접 사용합니다.

# === 이미지 업로드 ===
@router.post("/upload-image", summary="세계관 이미지 업로드")
async def upload_world_image(file: UploadFile = File(...)):
    """
    세계관 생성 화면에서 대표 이미지를 업로드하면 R2에 저장하고 URL과 메타를 반환
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
        meta = r2.upload_image(content, prefix="assets/world/", content_type=content_type)
        
        return {
            "image": meta["url"],
            "image_path": meta["path"],
            "src_file": meta["path"],
            "img_hash": hashlib.md5(content).hexdigest(),
            "key": meta["key"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# === AI 상세 생성 ===
class WorldBaseInfo(BaseModel):
    """세계관 기본 정보 (AI 생성용)"""
    name: str
    genre: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class WorldDetailResponse(BaseModel):
    """AI 생성된 세계관 상세 정보"""
    detail: str
    regions: List[str]
    factions: List[str]
    conflicts: str
    opening_scene: str
    style: str
    # 왼쪽 폼용 추천 값
    suggested_name: Optional[str] = None
    suggested_genre: Optional[str] = None
    suggested_summary: Optional[str] = None
    suggested_tags: List[str] = Field(default_factory=list)

@router.post("/ai-detail", response_model=WorldDetailResponse, summary="AI로 세계관 상세 생성")
async def ai_generate_world_detail(payload: WorldBaseInfo):
    """
    세계관 기본 정보를 바탕으로 상세 설정을 AI가 생성합니다.
    """
    # 필드 존재 여부 확인 (함수 시작 부분에서 정의하여 모든 곳에서 접근 가능)
    has_name = bool(payload.name and payload.name.strip())
    has_genre = bool(payload.genre and payload.genre.strip())
    has_summary = bool(payload.summary and payload.summary.strip())
    has_tags = len(payload.tags) > 0
    
    if not has_name:
        raise HTTPException(status_code=400, detail="World name is required")
    
    try:
        # 프롬프트 구성
        tags_str = ", ".join(payload.tags) if payload.tags else "없음"
        suggested_tags_json = json.dumps(payload.tags if payload.tags else ["판타지", "모험", "마법"])
        
        prompt = f"""다음 정보를 바탕으로 TRPG 세계관의 상세 설정을 생성해주세요.

세계관 이름: {payload.name}
장르: {payload.genre or "미정"}
한 줄 요약: {payload.summary or "없음"}
태그: {tags_str}

다음 JSON 형식으로 응답해주세요:
{{
  "detail": "세계관의 전반적인 설명 (3-5문장)",
  "regions": ["지역1", "지역2", "지역3"],
  "factions": ["세력1", "세력2", "세력3"],
  "conflicts": "주요 갈등과 대립 구조 (3-5문장)",
  "opening_scene": "TRPG 시작 장면 설명 (3-5문장)",
  "style": "세계관의 톤과 분위기 (예: 어둡고 신비로운 분위기, 마법과 기술이 공존하는 세계)",
  "suggested_name": "{payload.name}",
  "suggested_genre": "{payload.genre or "판타지"}",
  "suggested_summary": "{payload.summary or "한 줄 요약"}",
  "suggested_tags": {suggested_tags_json}
}}

반드시 유효한 JSON만 반환하고, 다른 설명은 포함하지 마세요."""
        
        # OpenAI 호출
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates TRPG world details in JSON format. Always respond with valid JSON only."},
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
                "detail": f"{payload.name}의 세계관 설명입니다.",
                "regions": ["주요 지역1", "주요 지역2"],
                "factions": ["주요 세력1", "주요 세력2"],
                "conflicts": "주요 갈등 구조입니다.",
                "opening_scene": "모험이 시작되는 장면입니다.",
                "style": "판타지 분위기",
                "suggested_name": payload.name,
                "suggested_genre": payload.genre or "판타지",
                "suggested_summary": payload.summary or "한 줄 요약",
                "suggested_tags": payload.tags if payload.tags else ["판타지", "모험", "마법"],
            }
        
        # 응답 생성 (has_name 등 변수는 함수 시작 부분에서 정의되어 있음)
        return WorldDetailResponse(
            detail=data.get("detail", ""),
            regions=data.get("regions", []),
            factions=data.get("factions", []),
            conflicts=data.get("conflicts", ""),
            opening_scene=data.get("opening_scene", ""),
            style=data.get("style", ""),
            suggested_name=data.get("suggested_name") if not has_name else None,
            suggested_genre=data.get("suggested_genre") if not has_genre else None,
            suggested_summary=data.get("suggested_summary") if not has_summary else None,
            suggested_tags=data.get("suggested_tags", []) if not has_tags else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("AI generation failed")
        # 에러 메시지에서 변수 참조를 피하기 위해 직접 문자열 사용
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"AI generation error details: {error_msg}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {error_msg}")

# === 세계관 생성 ===
class WorldMeta(BaseModel):
    """세계관 생성 메타데이터 모델"""
    model_config = ConfigDict(extra='ignore')
    
    id: Optional[int] = None
    name: str
    genre: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    image_path: Optional[str] = None
    src_file: Optional[str] = None
    img_hash: Optional[str] = None
    detail: Optional[str] = None
    regions: Optional[List[str]] = None
    factions: Optional[List[str]] = None
    conflicts: Optional[str] = None
    opening_scene: Optional[str] = None
    style: Optional[str] = None
    status: Optional[str] = "active"
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    reg_user: Optional[str] = Field(default=None, description="등록한 사용자의 google_id 또는 email")

@router.post("", summary="세계관 생성")
async def create_world(
    file: UploadFile = File(...),
    meta: str = Form(...),
    db = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    세계관 이미지와 메타데이터를 함께 받아 R2 업로드 + Mongo 저장.
    - file: 세계관 이미지 파일
    - meta: JSON 문자열 (WorldMeta 구조)
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
        
        # boolean을 문자열로 변환 (DB에서 "Y"/"N" 또는 True/False로 올 수 있음)
        if isinstance(is_use, bool):
            is_use = "Y" if is_use else "N"
        if isinstance(is_lock, bool):
            is_lock = "Y" if is_lock else "N"
        
        # 사용 불가
        if is_use is not None and is_use != "Y":
            raise HTTPException(status_code=403, detail="현재 사용이 불가한 상태입니다.")
        
        # 계정 잠금
        if is_lock is not None and is_lock == "Y":
            raise HTTPException(status_code=403, detail="현재 계정이 차단된 상태입니다.")
        
        # 1) meta 파싱
        try:
            payload = WorldMeta.model_validate_json(meta)
        except Exception as e:
            logger.error(f"Failed to parse meta JSON: {e}")
            raise HTTPException(status_code=400, detail="세계관 정보(meta)가 올바르지 않습니다.")
        
        if not payload.name or not payload.name.strip():
            raise HTTPException(status_code=400, detail="세계관 이름을 입력해주세요.")
        
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
            image_meta = r2.upload_image(content, prefix="assets/world/", content_type=content_type)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"[R2_UPLOAD_ERROR] {e}")
            raise HTTPException(status_code=502, detail="이미지 업로드 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
        
        # 5) MongoDB 저장
        try:
            # 1) id 자동 증가: 가장 큰 id + 1
            new_id = get_next_world_id(db)
            
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
            
            doc = {
                "id": new_id,
                "name": payload.name.strip(),
                "genre": payload.genre,
                "summary": payload.summary or "",
                "tags": payload.tags or [],
                "image": normalized_path,  # 내부 경로로 저장
                "image_path": normalized_path,  # 내부 경로로 저장
                "src_file": normalized_path,  # 내부 경로로 저장
                "img_hash": hashlib.md5(content).hexdigest(),
                "detail": payload.detail or "",
                "regions": payload.regions or [],
                "factions": payload.factions or [],
                "conflicts": payload.conflicts or "",
                "opening_scene": payload.opening_scene or "",
                "style": payload.style or "",
                "status": payload.status or "active",
                "reg_user": reg_user,  # 등록자 식별자
                "created_at": now,
                "updated_at": now,
            }
            
            result = db.worlds.insert_one(doc)
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
            raise HTTPException(status_code=500, detail="세계관 정보를 저장하는 중 서버 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("World creation failed")
        raise HTTPException(status_code=500, detail="세계관 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

# ===== MongoDB 연결 (간단 버전) =====
_MONGO_CLIENT: AsyncIOMotorClient | None = None

def get_mongo_db():
    """
    기존 프로젝트에 전용 Mongo 헬퍼가 있으면 그걸 써도 되는데,
    여기서는 worlds 목록용으로만 쓰는 간단 헬퍼를 둔다.
    """
    global _MONGO_CLIENT
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "arcanaverse")
    if not mongo_uri:
        # 환경변수 설정이 안돼 있으면 바로 에러 내버리기
        raise RuntimeError("MONGO_URI env var is not set")
    if _MONGO_CLIENT is None:
        _MONGO_CLIENT = AsyncIOMotorClient(mongo_uri)
    return _MONGO_CLIENT[db_name]

# ===== Pydantic 모델 =====
class World(BaseModel):
    """
    world 컬렉션 한 개 문서.
    실제 필드는 Mongo 에 있는 그대로 extra 허용해서 받는다.
    (id, name, genre, image, image_path, status, ... 등)
    """
    model_config = ConfigDict(extra="allow")
    # Mongo 문서 안에 이미 id(숫자) 필드를 쓰고 있으니 그걸 그대로 씀
    id: int | str = Field(..., description="세계관 ID")
    name: str = Field(..., description="세계관 이름")

class WorldListResponse(BaseModel):
    total: int
    items: list[World]

# ===== 라우터 =====
@router.get("", response_model=WorldListResponse)
async def list_worlds(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(None, description="이름/태그/요약 검색어"),
):
    """
    세계관 목록 조회.

    - 기본: created_at DESC 정렬
    - q 가 있으면 name / tags / summary 에 대한 부분 일치(case-insensitive) 검색

    프론트에서는 /v1/worlds?offset=0&limit=200[&q=검색어] 형태로 호출하고,
    응답은 { total: number, items: World[] } 형태를 기대하고 있음.
    """
    db = get_mongo_db()
    coll = db["worlds"]

    # 검색어 전처리
    if q is not None:
        q = q.strip()
        if q == "":
            q = None

    # 필요하면 status="active" 조건만 주기
    base_query: Dict[str, Any] = {}  # 예: {"status": "active"}

    if q:
        # name / tags / summary 에 대해 부분 일치 검색
        search_filter: Dict[str, Any] = {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
                {"summary": {"$regex": q, "$options": "i"}},
            ]
        }
        query: Dict[str, Any] = {**base_query, **search_filter}
    else:
        query = base_query

    total = await coll.count_documents(query)
    cursor = (
        coll.find(query)
        .sort("created_at", -1)  # 최신순
        .skip(offset)
        .limit(limit)
    )
    items: list[World] = []
    async for doc in cursor:
        # _id(ObjectId)는 프론트에서 쓰지 않으니 제거
        doc.pop("_id", None)
        # 이미지 경로를 R2 public URL로 정규화 (캐릭터 API와 동일하게)
        if "image" in doc:
            doc["image"] = normalize_world_image(doc.get("image"))
        if "image_path" in doc:
            doc["image_path"] = normalize_world_image(doc.get("image_path"))
        if "src_file" in doc:
            doc["src_file"] = normalize_world_image(doc.get("src_file"))
        items.append(World(**doc))
    return WorldListResponse(total=total, items=items)

@router.get("/{world_id}", response_model=World)
async def get_world(world_id: str):
    """
    단일 세계관 조회
    - 숫자 ID 또는 world_XX 형태 모두 허용
    """
    try:
        # world_id를 숫자로 변환 시도
        wid = world_id
        if isinstance(wid, str) and wid.startswith("world_"):
            try:
                wid = int(wid.split("_", 1)[1])
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid world id")
        wid = int(wid)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid world id")
    
    db = get_mongo_db()
    coll = db["worlds"]
    
    # id로 조회 시도
    doc = await coll.find_one({"id": wid})
    if not doc:
        raise HTTPException(status_code=404, detail="World not found")
    
    # _id 제거
    doc.pop("_id", None)
    
    # 이미지 경로를 R2 public URL로 정규화
    if "image" in doc:
        doc["image"] = normalize_world_image(doc.get("image"))
    if "image_path" in doc:
        doc["image_path"] = normalize_world_image(doc.get("image_path"))
    if "src_file" in doc:
        doc["src_file"] = normalize_world_image(doc.get("src_file"))
    
    return World(**doc)

