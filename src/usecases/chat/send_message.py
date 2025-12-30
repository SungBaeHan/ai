# src/usecases/chat/send_message.py
"""
메시지 전송 유스케이스
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from src.ports.repositories.chat_repository import ChatRepository
from src.ports.services.llm_service import LLMService


class SendMessageUseCase:
    """메시지 전송 유스케이스"""
    
    def __init__(self, repository: ChatRepository, llm_service: LLMService):
        self.repository = repository
        self.llm_service = llm_service
    
    def execute(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str,
        content: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        메시지를 전송하고 LLM 응답을 생성합니다.
        
        Args:
            user_id: 사용자 ID (google_id)
            chat_type: 채팅 타입 ("character" | "world" | "game")
            entity_id: 엔티티 ID
            content: 메시지 내용
            request_id: 요청 ID (중복 방지용, 선택사항)
        
        Returns:
            {
                "session": 업데이트된 세션 정보 (dict),
                "messages": 생성된 메시지 리스트 [user_msg, assistant_msg] (list)
            }
        """
        now = datetime.now(timezone.utc)
        
        # 1) 세션 생성 또는 조회 (upsert)
        session = self.repository.upsert_session(
            user_id=user_id,
            chat_type=chat_type,
            entity_id=str(entity_id),
            defaults={},
        )
        session_id_str = session["_id"]
        session_id = ObjectId(session_id_str) if isinstance(session_id_str, str) else session_id_str
        
        # 2) 사용자 메시지 삽입
        user_msg = self.repository.insert_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=content,
            request_id=request_id,
        )
        
        # 3) 세션 상태를 busy로 업데이트
        self.repository.update_session(
            session_id=session_id,
            patch={
                "status": "busy",
                "last_message_at": now,
                "last_message_preview": content[:80] if content else None,
                "last_event_at": now,
            },
            inc_state_version=True,
        )
        
        # 4) 상태 변경 이벤트 기록
        user_msg_id_str = user_msg["_id"]
        user_msg_id = ObjectId(user_msg_id_str) if isinstance(user_msg_id_str, str) else user_msg_id_str
        self.repository.insert_event(
            session_id=session_id,
            user_id=user_id,
            event_type="status_changed",
            payload={"status": "busy"},
            message_id=user_msg_id,
        )
        
        # 5) LLM 호출
        # 기존 메시지 히스토리 조회 (컨텍스트 구성용)
        existing_messages = self.repository.list_messages(session_id, limit=50)
        
        # 메시지 리스트 구성 (role/content 형태)
        messages = []
        for msg in existing_messages:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        
        # LLM 호출
        try:
            llm_reply = self.llm_service.generate_reply(messages=messages)
        except Exception as e:
            # LLM 호출 실패 시 에러 메시지
            llm_reply = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
        
        # 6) 어시스턴트 메시지 삽입
        assistant_msg = self.repository.insert_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=llm_reply,
        )
        
        # 7) 세션 상태를 idle로 업데이트
        updated_session = self.repository.update_session(
            session_id=session_id,
            patch={
                "status": "idle",
                "last_message_at": now,
                "last_message_preview": llm_reply[:80] if llm_reply else None,
                "last_event_at": now,
            },
            inc_state_version=True,
        )
        
        # 8) 상태 변경 이벤트 기록
        assistant_msg_id_str = assistant_msg["_id"]
        assistant_msg_id = ObjectId(assistant_msg_id_str) if isinstance(assistant_msg_id_str, str) else assistant_msg_id_str
        self.repository.insert_event(
            session_id=session_id,
            user_id=user_id,
            event_type="status_changed",
            payload={"status": "idle"},
            message_id=assistant_msg_id,
        )
        
        # 9) 반환
        return {
            "session": updated_session,
            "messages": [user_msg, assistant_msg],
        }

