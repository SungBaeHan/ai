# ========================================
# apps/api/routes/games.py — 게임 API
# - POST /v1/games : 게임 생성
# - GET /v1/games : 게임 목록 조회
# - GET /v1/games/{game_id} : 게임 상세 조회
# - GET /v1/games/health : 헬스 체크
# ========================================

import time
import logging
import hashlib
import json
from copy import deepcopy
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, status
from adapters.persistence.mongo import get_db
from adapters.file_storage.r2_storage import R2Storage
from apps.api.routes.worlds import get_current_user_v2
from apps.api.deps.user_snapshot import build_owner_ref_info
from apps.api.utils import build_public_image_url, build_public_image_url_from_path
from apps.core.utils.assets import normalize_asset_path
from apps.api.models.games import (
    GameCreateRequest,
    GameResponse,
    GameCharacter,
    WorldSnapshot,
    CharacterSnapshot,
    GameRulesConfig,
)
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
from pymongo.database import Database

logger = logging.getLogger(__name__)

router = APIRouter()  # 서브 라우터

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

def normalize_image_path(image_url: Optional[str]) -> str:
    """
    R2 공개 URL을 내부 저장 경로('/assets/...')로 변환한다.
    
    - 예: 'https://pub-xxxx.r2.dev/assets/game/abcd.png'
      → '/assets/game/abcd.png'
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

def get_next_game_id(db: Database) -> int:
    """
    games 컬렉션에서 가장 큰 id 값을 찾아 +1 해서 반환한다.
    
    - 문서가 없다면 1부터 시작한다.
    """
    doc = db.games.find_one({}, sort=[("id", -1)])
    if doc and "id" in doc:
        try:
            return int(doc["id"]) + 1
        except (TypeError, ValueError):
            # id가 이상한 값이어도 최소한 1부터 시작하도록
            pass
    return 1

def _normalize_tags(raw: Any) -> List[str]:
    """
    CharacterSnapshot.tags 에 들어갈 값을 항상 List[str] 로 맞춰준다.
    
    - None -> []
    - list -> 각 요소를 str 로 캐스팅
    - JSON 문자열 '["a","b"]' -> 파싱 후 리스트
    - 그 외 str/기타 타입 -> [str(raw)]
    """
    if raw is None:
        return []
    
    if isinstance(raw, list):
        return [str(item) for item in raw]
    
    if isinstance(raw, str):
        # JSON 배열 문자열인 경우 우선 파싱 시도
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [str(item) for item in loaded]
        except Exception:
            # 파싱 실패하면 그냥 하나짜리 리스트로
            return [raw]
        # loaded 가 리스트가 아니면 역시 하나짜리 리스트
        return [str(loaded)]
    
    # 나머지 타입은 전부 문자열로 감싸서 단일 리스트로
    return [str(raw)]

@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED, summary="게임 생성")
async def create_game(
    file: Optional[UploadFile] = File(None),
    meta: str = Form(...),
    db: Database = Depends(get_db),
    current_user = Depends(get_current_user_v2),
):
    """
    게임 생성 엔드포인트.
    
    프론트에서 넘어온 FormData를 받아서:
    - file: 배경 이미지 파일 (선택사항)
    - meta: JSON 문자열 (GameCreateRequest 구조)
    
    이미지가 있으면 R2에 업로드하고, MongoDB games 컬렉션에 저장한다.
    world_snapshot과 character snapshots를 자동으로 생성하여 저장한다.
    """
    try:
        # --- 로그인 및 사용 가능 여부 체크 ---
        if current_user is None:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        is_use = current_user.get("is_use") or current_user.get("isUse")
        is_lock = current_user.get("is_lock") or current_user.get("isLock")
        
        # boolean을 문자열로 변환
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
        
        # 1) meta 파싱 및 검증
        try:
            payload_dict = json.loads(meta)
            payload = GameCreateRequest(**payload_dict)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse meta JSON: {e}")
            raise HTTPException(status_code=400, detail="게임 정보(meta)가 올바르지 않습니다.")
        
        # 2) 세계관 조회 및 스냅샷 생성
        world_doc = db.worlds.find_one({"id": payload.world_ref_id})
        if not world_doc:
            raise HTTPException(status_code=400, detail=f"세계관을 찾을 수 없습니다. (id: {payload.world_ref_id})")
        
        # world_snapshot 생성
        world_image_url = build_public_image_url(
            world_doc.get("image") or world_doc.get("image_path"),
            prefix="world"
        )
        # 이미지 URL을 상대 경로로 정규화
        normalized_world_image_url = normalize_asset_path(world_image_url)
        world_snapshot = WorldSnapshot(
            id=world_doc.get("id"),
            name=world_doc.get("name"),
            summary=world_doc.get("summary"),
            tags=world_doc.get("tags", []),
            image_url=normalized_world_image_url,
            img_hash=world_doc.get("img_hash"),
        ).model_dump()
        
        # 3) rules.attributes를 딕셔너리로 변환 (attributes_base로 사용)
        base_attributes = None
        if hasattr(payload.rules, "attributes") and payload.rules.attributes:
            try:
                # payload.rules.attributes는 Dict[str, GameRuleAttributesConfig] 형태
                # 각 GameRuleAttributesConfig를 dict로 변환
                base_attributes = {}
                for key, value in payload.rules.attributes.items():
                    if hasattr(value, "model_dump"):
                        # Pydantic 모델이면 dict로 변환
                        base_attributes[key] = value.model_dump()
                    elif isinstance(value, dict):
                        # 이미 dict 형태면 그대로 사용
                        base_attributes[key] = deepcopy(value)
                    else:
                        # 기타 타입은 그대로 사용
                        base_attributes[key] = value
            except Exception as e:
                logger.warning(f"Failed to convert rules.attributes to dict: {e}")
                base_attributes = None
        
        # 4) 캐릭터 조회 및 스냅샷 생성
        char_ids = [c.char_ref_id for c in payload.characters]
        char_docs: Dict[int, Dict[str, Any]] = {}
        
        if char_ids:
            for doc in db.characters.find({"id": {"$in": char_ids}}):
                char_docs[doc.get("id")] = doc
        
        game_characters: List[Dict[str, Any]] = []
        for c in payload.characters:
            doc = char_docs.get(c.char_ref_id)
            if not doc:
                raise HTTPException(
                    status_code=400,
                    detail=f"캐릭터를 찾을 수 없습니다. (id: {c.char_ref_id})",
                )
            
            char_image_url = build_public_image_url(
                doc.get("image") or doc.get("image_path"),
                prefix="char"
            )
            # 이미지 URL을 상대 경로로 정규화
            normalized_char_image_url = normalize_asset_path(char_image_url)
            
            # snapshot 딕셔너리 생성
            snapshot_dict = {
                "id": doc.get("id"),
                "name": doc.get("name"),
                "summary": doc.get("summary"),
                "tags": _normalize_tags(doc.get("tags")),
                "image_url": normalized_char_image_url,
                "archetype": doc.get("archetype"),
            }
            
            # attributes_base를 rules.attributes로 설정 (깊은 복사)
            if base_attributes is not None:
                snapshot_dict["attributes_base"] = deepcopy(base_attributes)
            
            snapshot = CharacterSnapshot(**snapshot_dict).model_dump()
            
            game_characters.append(
                GameCharacter(
                    char_ref_id=c.char_ref_id,
                    role=c.role,
                    snapshot=snapshot,
                ).model_dump()
            )
        
        # 4) 이미지 처리 (선택사항)
        image_path = payload.background_image_path
        img_hash = payload.img_hash
        if file:
            content = await file.read()
            if content:
                # Content-Type 확인
                content_type = file.content_type or "image/png"
                if not content_type.startswith("image/"):
                    content_type = "image/png"
                
                # R2 업로드
                try:
                    r2 = get_r2_storage()
                    image_meta = r2.upload_image(content, prefix="assets/game/", content_type=content_type)
                    # 이미지 경로를 상대 경로로 정규화
                    raw_image_path = normalize_image_path(image_meta["url"])
                    image_path = normalize_asset_path(raw_image_path)
                    img_hash = hashlib.md5(content).hexdigest()
                except HTTPException:
                    raise
                except Exception as e:
                    logger.exception(f"[R2_UPLOAD_ERROR] {e}")
                    raise HTTPException(status_code=502, detail="이미지 업로드 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
        
        # 5) MongoDB 저장
        try:
            # id 자동 증가
            new_id = get_next_game_id(db)
            
            # 타임스탬프 설정 (datetime.utcnow() 사용 - ISODate 형식)
            now = datetime.now(timezone.utc)
            
            # 등록자(reg_user) 정보 세팅
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
            
            # 게임 문서 생성
            game_doc = {
                "id": new_id,
                "title": payload.title,
                "world_ref_id": payload.world_ref_id,
                "world_snapshot": world_snapshot,
                "scenario_summary": payload.scenario_summary,
                "scenario_detail": payload.scenario_detail,
                "tags": payload.tags or [],
                "characters": game_characters,
                "rules": payload.rules.model_dump(),
                "background_image_path": normalize_asset_path(image_path) if image_path else None,
                "img_hash": img_hash,
                "status": "active",
                "reg_user": reg_user,
                "created_at": now,
                "updated_at": now,
            }
            
            # MongoDB에 저장
            result = db.games.insert_one(game_doc)
            game_doc["_id"] = result.inserted_id
            
            # GameResponse로 변환하여 반환
            return GameResponse(**game_doc)
        except Exception as e:
            logger.exception(f"[MONGO_INSERT_ERROR] {e}")
            raise HTTPException(status_code=500, detail="게임 정보를 저장하는 중 서버 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Game creation failed")
        raise HTTPException(status_code=500, detail="게임 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

class GameListResponse(BaseModel):
    """게임 목록 응답 모델 (캐릭터/세계관과 동일한 구조)"""
    total: int
    items: List[GameResponse]
    offset: int = 0
    limit: int = 20


def to_public_url(path: Optional[str]) -> Optional[str]:
    """
    이미지 경로를 R2 public URL로 변환합니다.
    
    Args:
        path: 이미지 경로 (상대 경로 또는 절대 URL)
    
    Returns:
        R2 public URL 또는 None
    """
    if not path:
        return None
    if isinstance(path, str) and (path.startswith("http://") or path.startswith("https://")):
        return path
    return build_public_image_url_from_path(path)


def enrich_game_asset_urls(game: GameResponse) -> GameResponse:
    """
    게임 응답 객체의 이미지 경로를 R2 public URL로 변환합니다.
    
    Args:
        game: GameResponse 객체
    
    Returns:
        이미지 URL이 변환된 GameResponse 객체
    """
    # 1) 게임 배경 이미지: background_image_path -> background_image_url / image
    if game.background_image_path:
        public_bg = to_public_url(game.background_image_path)
        game.background_image_url = public_bg
        # 게임 카드/상세 공통으로 쓸 alias
        game.image = public_bg
    
    # 2) 월드 스냅샷 이미지: /assets/world/... -> public URL
    if game.world_snapshot and game.world_snapshot.image_url:
        game.world_snapshot.image_url = to_public_url(game.world_snapshot.image_url)
    
    # 3) 캐릭터 스냅샷 이미지: /assets/char/... -> public URL
    if game.characters:
        for entry in game.characters:
            if entry.snapshot and entry.snapshot.image_url:
                entry.snapshot.image_url = to_public_url(entry.snapshot.image_url)
    
    return game

@router.get("", response_model=GameListResponse, summary="게임 목록 조회")
async def list_games(
    offset: int = Query(0, ge=0, alias="offset"),
    limit: int = Query(20, ge=1, le=200, alias="limit"),
    db: Database = Depends(get_db),
):
    """
    게임 목록 조회 (created_at DESC 기준 정렬)
    캐릭터/세계관과 동일한 응답 구조: { total, items, offset, limit }
    """
    # 전체 개수 조회
    total = db.games.count_documents({})
    
    # 게임 목록 조회
    cursor = (
        db.games
        .find({})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    
    items: List[GameResponse] = []
    for doc in cursor:
        # created_at이 epoch seconds인 경우 datetime으로 변환
        if isinstance(doc.get("created_at"), (int, float)):
            doc["created_at"] = datetime.fromtimestamp(doc["created_at"], tz=timezone.utc)
        elif doc.get("created_at") is None:
            doc["created_at"] = datetime.now(timezone.utc)
        
        if isinstance(doc.get("updated_at"), (int, float)):
            doc["updated_at"] = datetime.fromtimestamp(doc["updated_at"], tz=timezone.utc)
        elif doc.get("updated_at") is None:
            doc["updated_at"] = datetime.now(timezone.utc)
        
        # GameResponse 객체 생성
        game = GameResponse(**doc)
        # 이미지 URL을 R2 public URL로 변환
        game = enrich_game_asset_urls(game)
        items.append(game)
    
    return GameListResponse(total=total, items=items, offset=offset, limit=limit)

@router.get("/{game_id}", response_model=GameResponse, summary="게임 상세 조회")
async def get_game(
    game_id: int,
    db: Database = Depends(get_db),
):
    """
    게임 상세 조회
    """
    doc = db.games.find_one({"id": game_id})
    if not doc:
        raise HTTPException(status_code=404, detail="게임을 찾을 수 없습니다.")
    
    # created_at이 epoch seconds인 경우 datetime으로 변환
    if isinstance(doc.get("created_at"), (int, float)):
        doc["created_at"] = datetime.fromtimestamp(doc["created_at"], tz=timezone.utc)
    elif doc.get("created_at") is None:
        doc["created_at"] = datetime.now(timezone.utc)
    
    if isinstance(doc.get("updated_at"), (int, float)):
        doc["updated_at"] = datetime.fromtimestamp(doc["updated_at"], tz=timezone.utc)
    elif doc.get("updated_at") is None:
        doc["updated_at"] = datetime.now(timezone.utc)
    
    # GameResponse 객체 생성
    game = GameResponse(**doc)
    # 이미지 URL을 R2 public URL로 변환
    game = enrich_game_asset_urls(game)
    return game

@router.get("/{game_id}/session", summary="게임 세션 조회/생성")
async def get_or_create_game_session(
    game_id: int,
    current_user = Depends(get_current_user_v2),
    db: Database = Depends(get_db),
):
    """
    현재 유저 기준으로 game_session을 조회하거나, 없으면 새로 생성해서 반환한다.
    
    - 로그인 필수
    - 기존 세션이 있으면 반환
    - 없으면 게임 메타를 기반으로 새 세션 생성
    """
    # 로그인 체크
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    # 1) 기존 세션 조회
    session = db.game_session.find_one({
        "game_id": game_id,
        "owner_ref_info.user_ref_id": current_user.get("user_id"),
    })
    
    if session:
        # _id를 문자열로 변환하여 반환
        if "_id" in session:
            session["_id"] = str(session["_id"])
        return session
    
    # 2) 게임 메타 조회
    game = db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게임을 찾을 수 없습니다.",
        )
    
    # 3) owner_ref_info 스냅샷 생성
    owner_ref_info = build_owner_ref_info(current_user)
    
    # 4) 새로운 세션 도큐먼트 구성
    new_session = {
        "game_id": game_id,
        "owner_ref_info": owner_ref_info,
        "persona_ref_id": None,  # 페르조나 기능 확장용, 지금은 None
        
        "characters_info": [],   # 이후 캐릭터 선택 화면에서 채울 예정이면 일단 빈 배열
        "combat": {
            "in_combat": False,
            "monsters": [],
            "phase": "none",
        },
        "story_history": [],
        "turn": 0,
        
        "user_info": {
            "attributes": {
                "hp": {"current": 100, "max": 100, "base": 100},
                "mp": {"current": 80, "max": 80, "base": 80},
            },
            "items": {
                "gold": 0,
                "inventory": [],
            },
        },
        
        # games 컬렉션의 world_snapshot을 그대로 스냅샷으로 저장
        "world_snapshot": game.get("world_snapshot"),
    }
    
    result = db.game_session.insert_one(new_session)
    new_session["_id"] = str(result.inserted_id)
    
    return new_session


@router.get("/health")
async def games_health_check():
    """게임 API 헬스 체크 엔드포인트"""
    return {"status": "ok"}
