# src/usecases/chat/open_chat.py
"""
채팅 열기 유스케이스
"""

from typing import Dict, Any, Optional
from src.ports.repositories.chat_repository import ChatRepository
from bson import ObjectId


class OpenChatUseCase:
    """채팅 열기 유스케이스"""
    
    def __init__(self, repository: ChatRepository):
        self.repository = repository
    
    def execute(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        채팅 세션을 열고 메시지 목록을 조회합니다.
        
        Args:
            user_id: 사용자 ID (google_id)
            chat_type: 채팅 타입 ("character" | "world" | "game")
            entity_id: 엔티티 ID
            limit: 최대 메시지 개수
        
        Returns:
            {
                "session": 세션 정보 (dict 또는 None),
                "messages": 메시지 리스트 (list)
            }
        """
        # 세션 조회
        session = self.repository.get_session(user_id, chat_type, entity_id)
        
        if not session:
            return {
                "session": None,
                "messages": [],
            }
        
        # 메시지 목록 조회
        session_id_str = session["_id"]
        session_id = ObjectId(session_id_str) if isinstance(session_id_str, str) else session_id_str
        messages = self.repository.list_messages(session_id, limit=limit)
        
        # 세션 요약 정보만 반환 (필요한 필드만)
        session_summary = {
            "_id": session["_id"],
            "user_id": session.get("user_id"),
            "chat_type": session.get("chat_type"),
            "entity_id": session.get("entity_id"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "last_message_at": session.get("last_message_at"),
            "last_message_preview": session.get("last_message_preview"),
            "status": session.get("status"),
            "state_version": session.get("state_version"),
        }
        
        return {
            "session": session_summary,
            "messages": messages,
        }

