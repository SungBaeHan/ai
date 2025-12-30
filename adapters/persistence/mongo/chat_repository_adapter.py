# adapters/persistence/mongo/chat_repository_adapter.py
"""
MongoDB ChatRepository 어댑터
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from src.ports.repositories.chat_repository import ChatRepository
from adapters.persistence.mongo import get_db


class MongoChatRepository(ChatRepository):
    """MongoDB 구현체"""
    
    def __init__(self):
        self._db = None
        self._session_col = None
        self._message_col = None
        self._event_col = None
    
    def _ensure(self):
        """컬렉션 지연 초기화"""
        if self._db is None:
            self._db = get_db()
            self._session_col = self._db["chat_session"]
            self._message_col = self._db["chat_message"]
            self._event_col = self._db["chat_event"]
    
    def get_session(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        self._ensure()
        doc = self._session_col.find_one({
            "user_id": user_id,
            "chat_type": chat_type,
            "entity_id": str(entity_id),
        })
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    def upsert_session(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """세션 생성 또는 업데이트"""
        self._ensure()
        now = datetime.now(timezone.utc)
        
        filter_dict = {
            "user_id": user_id,
            "chat_type": chat_type,
            "entity_id": str(entity_id),
        }
        
        update_dict = {
            "$setOnInsert": {
                "user_id": user_id,
                "chat_type": chat_type,
                "entity_id": str(entity_id),
                "created_at": now,
                "state_version": 0,
            },
            "$set": {
                "updated_at": now,
                **(defaults or {}),
            },
        }
        
        result = self._session_col.find_one_and_update(
            filter_dict,
            update_dict,
            upsert=True,
            return_document=True,
        )
        
        # _id를 문자열로 변환
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        return result
    
    def update_session(
        self,
        session_id: ObjectId,
        patch: Dict[str, Any],
        inc_state_version: bool = True
    ) -> Dict[str, Any]:
        """세션 업데이트"""
        self._ensure()
        now = datetime.now(timezone.utc)
        
        update_dict = {
            "$set": {
                "updated_at": now,
                **patch,
            },
        }
        
        if inc_state_version:
            update_dict["$inc"] = {"state_version": 1}
        
        result = self._session_col.find_one_and_update(
            {"_id": session_id},
            update_dict,
            return_document=True,
        )
        
        if result and "_id" in result:
            result["_id"] = str(result["_id"])
        return result
    
    def list_messages(
        self,
        session_id: ObjectId,
        limit: int = 100,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """메시지 목록 조회"""
        self._ensure()
        query = {"session_id": session_id}
        
        if before:
            query["created_at"] = {"$lt": before}
        
        cursor = self._message_col.find(query).sort("created_at", 1).limit(limit)
        messages = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "session_id" in doc:
                doc["session_id"] = str(doc["session_id"])
            if "message_id" in doc:
                doc["message_id"] = str(doc["message_id"])
            messages.append(doc)
        
        return messages
    
    def insert_message(
        self,
        session_id: ObjectId,
        user_id: str,
        role: str,
        content: str,
        request_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """메시지 삽입 (중복 방지 지원)"""
        self._ensure()
        now = datetime.now(timezone.utc)
        
        # request_id가 있고 이미 존재하는 경우 조회해서 반환 (idempotency)
        if request_id:
            existing = self._message_col.find_one({
                "session_id": session_id,
                "request_id": request_id,
            })
            if existing:
                existing["_id"] = str(existing["_id"])
                existing["session_id"] = str(existing["session_id"])
                if "message_id" in existing:
                    existing["message_id"] = str(existing["message_id"])
                return existing
        
        message_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "created_at": now,
        }
        
        if request_id:
            message_doc["request_id"] = request_id
        if meta:
            message_doc["meta"] = meta
        
        # 유니크 인덱스가 없어도 중복 체크 후 삽입
        try:
            result = self._message_col.insert_one(message_doc)
            message_doc["_id"] = str(result.inserted_id)
            message_doc["session_id"] = str(session_id)
            return message_doc
        except Exception:
            # 중복 삽입 시도 시 기존 문서 조회
            if request_id:
                existing = self._message_col.find_one({
                    "session_id": session_id,
                    "request_id": request_id,
                })
                if existing:
                    existing["_id"] = str(existing["_id"])
                    existing["session_id"] = str(existing["session_id"])
                    if "message_id" in existing:
                        existing["message_id"] = str(existing["message_id"])
                    return existing
            raise
    
    def insert_event(
        self,
        session_id: ObjectId,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
        message_id: Optional[ObjectId] = None
    ) -> Dict[str, Any]:
        """이벤트 삽입"""
        self._ensure()
        now = datetime.now(timezone.utc)
        
        event_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": now,
        }
        
        if message_id:
            event_doc["message_id"] = message_id
        
        result = self._event_col.insert_one(event_doc)
        event_doc["_id"] = str(result.inserted_id)
        event_doc["session_id"] = str(session_id)
        if message_id:
            event_doc["message_id"] = str(message_id)
        return event_doc
    
    @staticmethod
    def ensure_indexes():
        """인덱스 생성 (startup 시 호출)"""
        from adapters.persistence.mongo import get_db
        db = get_db()
        
        # chat_session 컬렉션 인덱스
        session_col = db["chat_session"]
        try:
            # UNIQUE(user_id, chat_type, entity_id)
            session_col.create_index(
                [("user_id", 1), ("chat_type", 1), ("entity_id", 1)],
                unique=True,
                name="chat_session_uniq_user_type_entity"
            )
            # (user_id, updated_at desc)
            session_col.create_index(
                [("user_id", 1), ("updated_at", -1)],
                name="chat_session_idx_user_updated"
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to create chat_session indexes: {e}")
        
        # chat_message 컬렉션 인덱스
        message_col = db["chat_message"]
        try:
            # (session_id, created_at asc)
            message_col.create_index(
                [("session_id", 1), ("created_at", 1)],
                name="chat_message_idx_session_created"
            )
            # (session_id, request_id) 부분 유니크 (request_id가 null이 아닌 경우만)
            # MongoDB는 부분 유니크 인덱스를 직접 지원하지 않으므로, 
            # 애플리케이션 레벨에서 중복 체크 (insert_message에서 처리)
            message_col.create_index(
                [("session_id", 1), ("request_id", 1)],
                name="chat_message_idx_session_request",
                partialFilterExpression={"request_id": {"$exists": True, "$ne": None}}
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to create chat_message indexes: {e}")
        
        # chat_event 컬렉션 인덱스
        event_col = db["chat_event"]
        try:
            # (session_id, created_at desc)
            event_col.create_index(
                [("session_id", 1), ("created_at", -1)],
                name="chat_event_idx_session_created"
            )
            # (session_id, event_type, created_at desc)
            event_col.create_index(
                [("session_id", 1), ("event_type", 1), ("created_at", -1)],
                name="chat_event_idx_session_type_created"
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to create chat_event indexes: {e}")

