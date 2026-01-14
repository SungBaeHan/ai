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
    
    # chat_session, chat_message, chat_event 컬렉션 인덱스
    try:
        from adapters.persistence.mongo.chat_repository_adapter import MongoChatRepository
        MongoChatRepository.ensure_indexes()
    except Exception as e:
        # 인덱스 생성 실패는 로그만 남기고 계속 진행
        import logging
        logging.warning(f"Failed to create chat indexes: {e}")
    
    # worlds_session, worlds_message, worlds_event 컬렉션 인덱스
    try:
        ensure_world_chat_indexes(db)
    except Exception as e:
        # 인덱스 생성 실패는 로그만 남기고 계속 진행
        import logging
        logging.warning(f"Failed to create world chat indexes: {e}")
    
    return {"ok": True, "created": True}


def ensure_world_chat_indexes(db):
    """World Chat 컬렉션 인덱스 생성"""
    import logging
    logger = logging.getLogger(__name__)
    
    # worlds_session 컬렉션 인덱스
    session_col = db["worlds_session"]
    try:
        # UNIQUE(user_id, chat_type, entity_id)
        session_col.create_index(
            [("user_id", 1), ("chat_type", 1), ("entity_id", 1)],
            unique=True,
            name="worlds_session_uniq_user_type_entity"
        )
        # (user_id, updated_at desc)
        session_col.create_index(
            [("user_id", 1), ("updated_at", -1)],
            name="worlds_session_idx_user_updated"
        )
        logger.info("Created indexes for worlds_session collection")
    except Exception as e:
        logger.warning(f"Failed to create worlds_session indexes (may already exist): {e}")
    
    # worlds_message 컬렉션 인덱스
    message_col = db["worlds_message"]
    try:
        # (session_id, created_at asc)
        message_col.create_index(
            [("session_id", 1), ("created_at", 1)],
            name="worlds_message_idx_session_created"
        )
        # (session_id, request_id) partial unique (request_id가 null이 아닌 경우만)
        message_col.create_index(
            [("session_id", 1), ("request_id", 1)],
            name="worlds_message_idx_session_request",
            partialFilterExpression={"request_id": {"$exists": True, "$ne": None}}
        )
        logger.info("Created indexes for worlds_message collection")
    except Exception as e:
        logger.warning(f"Failed to create worlds_message indexes (may already exist): {e}")
    
    # worlds_event 컬렉션 인덱스
    event_col = db["worlds_event"]
    try:
        # (session_id, created_at desc)
        event_col.create_index(
            [("session_id", 1), ("created_at", -1)],
            name="worlds_event_idx_session_created"
        )
        # (session_id, event_type, created_at desc)
        event_col.create_index(
            [("session_id", 1), ("event_type", 1), ("created_at", -1)],
            name="worlds_event_idx_session_type_created"
        )
        logger.info("Created indexes for worlds_event collection")
    except Exception as e:
        logger.warning(f"Failed to create worlds_event indexes (may already exist): {e}")

