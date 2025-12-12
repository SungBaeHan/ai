import os
from typing import Optional
try:
    from adapters.persistence.mongo.character_repository_adapter import MongoCharacterRepository
except Exception:
    MongoCharacterRepository = None


def init_mongo_indexes() -> Optional[dict]:
    """Create commonly used indexes for Mongo collections."""
    # DB_BACKEND 우선, 없으면 DATA_BACKEND (하위 호환성), 기본값은 mongo
    backend = os.getenv("DB_BACKEND") or os.getenv("DATA_BACKEND", "mongo")
    backend = backend.lower()
    if backend != "mongo":
        return None

    from adapters.persistence.mongo import get_db
    db = get_db()
    
    # characters 컬렉션 인덱스
    if MongoCharacterRepository:
        repo = MongoCharacterRepository()
        col = repo.collection
        # 1) 고유 키: id
        col.create_index("id", unique=True, name="uniq_id")
        # 2) 자주 조회할 필드들에 보조 인덱스 (필요시 주석 해제)
        # col.create_index("archetype", name="idx_archetype")
        # col.create_index("created_at", name="idx_created_at")
        # 3) 텍스트 검색 (name, tags, summary 등)
        # col.create_index([("name","text"), ("tags","text"), ("summary","text")], name="txt_search")
    
    # games 컬렉션 인덱스
    try:
        games_col = db.games
        games_col.create_index("id", unique=True, name="games_uniq_id")
        games_col.create_index("reg_user", name="games_idx_reg_user")
        games_col.create_index("world_ref_id", name="games_idx_world_ref_id")
        games_col.create_index("status", name="games_idx_status")
    except Exception as e:
        # 인덱스 생성 실패는 로그만 남기고 계속 진행
        import logging
        logging.warning(f"Failed to create games indexes: {e}")
    
    # game_session 컬렉션 인덱스
    try:
        game_session_col = db.game_session
        # game_id와 owner_ref_info.user_ref_id 복합 인덱스
        game_session_col.create_index(
            [("game_id", 1), ("owner_ref_info.user_ref_id", 1)],
            name="game_session_idx_game_user"
        )
    except Exception as e:
        # 인덱스 생성 실패는 로그만 남기고 계속 진행
        import logging
        logging.warning(f"Failed to create game_session indexes: {e}")
    
    return {"ok": True, "created": True}

