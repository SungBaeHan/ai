# apps/api/services/chat_persist.py
"""
채팅 저장 서비스
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pymongo.database import Database
from bson import ObjectId

logger = logging.getLogger(__name__)


def persist_character_chat(
    db: Database,
    trace_id: str,
    user_id: str,
    character_id: str,
    payload: Dict[str, Any],
    llm_answer: str
) -> Dict[str, Any]:
    """
    캐릭터 채팅을 MongoDB에 저장합니다.
    
    Args:
        db: MongoDB 데이터베이스 인스턴스
        trace_id: 트레이스 ID
        user_id: 사용자 ID (google_id)
        character_id: 캐릭터 ID (문자열 또는 정수)
        payload: 요청 페이로드
        llm_answer: LLM 응답 텍스트
    
    Returns:
        저장 결과 딕셔너리
        {
            "ok": bool,
            "writes": {
                "session": {...},
                "message": {...},
                "event": {...}
            }
        }
    
    Raises:
        Exception: 저장 실패 시
    """
    try:
        now = datetime.now(timezone.utc)
        character_id_str = str(character_id)
        writes = {}
        
        # 1) characters_session 컬렉션에 세션 저장/업데이트 (upsert)
        session_col = db["characters_session"]
        session_filter = {
            "user_id": user_id,
            "chat_type": "character",
            "entity_id": character_id_str,
        }
        session_update = {
            "$setOnInsert": {
                "user_id": user_id,
                "chat_type": "character",
                "entity_id": character_id_str,
                "created_at": now,
                "state_version": 0,
            },
            "$set": {
                "updated_at": now,
                "last_message_at": now,
                "last_message_preview": payload.get("message", "")[:80] if payload.get("message") else None,
                "status": "idle",
            },
        }
        session_result = session_col.update_one(session_filter, session_update, upsert=True)
        writes["session"] = {
            "matched": session_result.matched_count,
            "modified": session_result.modified_count,
            "upserted_id": str(session_result.upserted_id) if session_result.upserted_id else None,
        }
        logger.info(
            "[CHAT][DB] trace=%s col=characters_session op=update_one matched=%d modified=%d upserted_id=%s",
            trace_id,
            session_result.matched_count,
            session_result.modified_count,
            str(session_result.upserted_id) if session_result.upserted_id else None,
        )
        
        # upsert된 _id 또는 기존 세션의 _id 조회
        session_doc = session_col.find_one(session_filter)
        if not session_doc:
            raise Exception("Failed to create/find session after upsert")
        session_id = session_doc["_id"]
        
        # 2) characters_message 컬렉션에 사용자 메시지 저장
        message_col = db["characters_message"]
        user_message_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": payload.get("message", ""),
            "created_at": now,
        }
        user_msg_result = message_col.insert_one(user_message_doc)
        writes["user_message"] = {
            "inserted_id": str(user_msg_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=characters_message op=insert_one role=user inserted_id=%s",
            trace_id,
            str(user_msg_result.inserted_id),
        )
        
        # 3) characters_message 컬렉션에 어시스턴트 메시지 저장
        assistant_message_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": llm_answer,
            "created_at": now,
        }
        assistant_msg_result = message_col.insert_one(assistant_message_doc)
        writes["assistant_message"] = {
            "inserted_id": str(assistant_msg_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=characters_message op=insert_one role=assistant inserted_id=%s",
            trace_id,
            str(assistant_msg_result.inserted_id),
        )
        
        # 4) characters_event 컬렉션에 이벤트 저장 (선택사항)
        event_col = db["characters_event"]
        event_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "event_type": "message_sent",
            "payload": {
                "character_id": character_id_str,
                "message_length": len(payload.get("message", "")),
            },
            "created_at": now,
            "message_id": user_msg_result.inserted_id,
        }
        event_result = event_col.insert_one(event_doc)
        writes["event"] = {
            "inserted_id": str(event_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=characters_event op=insert_one inserted_id=%s",
            trace_id,
            str(event_result.inserted_id),
        )
        
        return {
            "ok": True,
            "writes": writes,
        }
    
    except Exception as e:
        logger.exception("[CHAT][DB][ERR] trace=%s error=%s", trace_id, str(e))
        raise


def persist_world_chat(
    db: Database,
    trace_id: str,
    user_id: str,
    world_id: str,
    payload: Dict[str, Any],
    llm_answer: str
) -> Dict[str, Any]:
    """
    세계관 채팅을 MongoDB에 저장합니다.
    
    Args:
        db: MongoDB 데이터베이스 인스턴스
        trace_id: 트레이스 ID
        user_id: 사용자 ID (google_id)
        world_id: 세계관 ID (문자열 또는 ObjectId)
        payload: 요청 페이로드
        llm_answer: LLM 응답 텍스트
    
    Returns:
        저장 결과 딕셔너리
        {
            "ok": bool,
            "writes": {
                "session": {...},
                "message": {...},
                "event": {...}
            }
        }
    
    Raises:
        Exception: 저장 실패 시
    """
    try:
        now = datetime.now(timezone.utc)
        world_id_str = str(world_id)
        writes = {}
        
        # 1) worlds_session 컬렉션에 세션 저장/업데이트 (upsert)
        session_col = db["worlds_session"]
        session_filter = {
            "user_id": user_id,
            "chat_type": "world",
            "entity_id": world_id_str,
        }
        session_update = {
            "$setOnInsert": {
                "user_id": user_id,
                "chat_type": "world",
                "entity_id": world_id_str,
                "created_at": now,
                "state_version": 0,
            },
            "$set": {
                "updated_at": now,
                "last_message_at": now,
                "last_message_preview": payload.get("message", "")[:80] if payload.get("message") else None,
                "status": "idle",
            },
        }
        session_result = session_col.update_one(session_filter, session_update, upsert=True)
        writes["session"] = {
            "matched": session_result.matched_count,
            "modified": session_result.modified_count,
            "upserted_id": str(session_result.upserted_id) if session_result.upserted_id else None,
        }
        logger.info(
            "[CHAT][DB] trace=%s col=worlds_session op=update_one matched=%d modified=%d upserted_id=%s",
            trace_id,
            session_result.matched_count,
            session_result.modified_count,
            str(session_result.upserted_id) if session_result.upserted_id else None,
        )
        
        # upsert된 _id 또는 기존 세션의 _id 조회
        session_doc = session_col.find_one(session_filter)
        if not session_doc:
            raise Exception("Failed to create/find session after upsert")
        session_id = session_doc["_id"]
        
        # 2) worlds_message 컬렉션에 사용자 메시지 저장
        message_col = db["worlds_message"]
        user_message_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": payload.get("message", ""),
            "created_at": now,
        }
        user_msg_result = message_col.insert_one(user_message_doc)
        writes["user_message"] = {
            "inserted_id": str(user_msg_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=worlds_message op=insert_one role=user inserted_id=%s",
            trace_id,
            str(user_msg_result.inserted_id),
        )
        
        # 3) worlds_message 컬렉션에 어시스턴트 메시지 저장
        assistant_message_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": llm_answer,
            "created_at": now,
        }
        assistant_msg_result = message_col.insert_one(assistant_message_doc)
        writes["assistant_message"] = {
            "inserted_id": str(assistant_msg_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=worlds_message op=insert_one role=assistant inserted_id=%s",
            trace_id,
            str(assistant_msg_result.inserted_id),
        )
        
        # 4) worlds_event 컬렉션에 이벤트 저장 (선택사항)
        event_col = db["worlds_event"]
        event_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "event_type": "message_sent",
            "payload": {
                "world_id": world_id_str,
                "message_length": len(payload.get("message", "")),
            },
            "created_at": now,
            "message_id": user_msg_result.inserted_id,
        }
        event_result = event_col.insert_one(event_doc)
        writes["event"] = {
            "inserted_id": str(event_result.inserted_id),
        }
        logger.info(
            "[CHAT][DB] trace=%s col=worlds_event op=insert_one inserted_id=%s",
            trace_id,
            str(event_result.inserted_id),
        )
        
        return {
            "ok": True,
            "writes": writes,
        }
    
    except Exception as e:
        logger.exception("[CHAT][DB][ERR] trace=%s error=%s", trace_id, str(e))
        raise

