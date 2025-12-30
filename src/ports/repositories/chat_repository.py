# src/ports/repositories/chat_repository.py
"""
ChatRepository 포트 (인터페이스)
Dependency Inversion Principle을 위한 채팅 저장소 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class ChatRepository(ABC):
    """채팅 저장소 인터페이스"""
    
    @abstractmethod
    def get_session(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        세션 조회
        
        Args:
            user_id: 사용자 ID (google_id)
            chat_type: 채팅 타입 ("character" | "world" | "game")
            entity_id: 엔티티 ID (문자열)
        
        Returns:
            세션 문서 (dict) 또는 None
        """
        pass
    
    @abstractmethod
    def upsert_session(
        self,
        user_id: str,
        chat_type: str,
        entity_id: str,
        defaults: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        세션 생성 또는 업데이트
        
        Args:
            user_id: 사용자 ID (google_id)
            chat_type: 채팅 타입 ("character" | "world" | "game")
            entity_id: 엔티티 ID (문자열)
            defaults: 기본값 (없으면 현재 시간 등 기본 필드 설정)
        
        Returns:
            세션 문서 (dict)
        """
        pass
    
    @abstractmethod
    def update_session(
        self,
        session_id: ObjectId,
        patch: Dict[str, Any],
        inc_state_version: bool = True
    ) -> Dict[str, Any]:
        """
        세션 업데이트
        
        Args:
            session_id: 세션 ObjectId
            patch: 업데이트할 필드들
            inc_state_version: state_version을 증가시킬지 여부
        
        Returns:
            업데이트된 세션 문서 (dict)
        """
        pass
    
    @abstractmethod
    def list_messages(
        self,
        session_id: ObjectId,
        limit: int = 100,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        메시지 목록 조회
        
        Args:
            session_id: 세션 ObjectId
            limit: 최대 개수
            before: 이 시간 이전의 메시지만 조회 (None이면 최신순)
        
        Returns:
            메시지 문서 리스트 (dict)
        """
        pass
    
    @abstractmethod
    def insert_message(
        self,
        session_id: ObjectId,
        user_id: str,
        role: str,
        content: str,
        request_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        메시지 삽입
        
        Args:
            session_id: 세션 ObjectId
            user_id: 사용자 ID (google_id)
            role: 역할 ("user" | "assistant" | "system" | "tool")
            content: 메시지 내용
            request_id: 요청 ID (중복 방지용, 선택사항)
            meta: 메타데이터 (선택사항)
        
        Returns:
            생성된 메시지 문서 (dict)
        """
        pass
    
    @abstractmethod
    def insert_event(
        self,
        session_id: ObjectId,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
        message_id: Optional[ObjectId] = None
    ) -> Dict[str, Any]:
        """
        이벤트 삽입
        
        Args:
            session_id: 세션 ObjectId
            user_id: 사용자 ID (google_id)
            event_type: 이벤트 타입 (예: "status_changed", "snapshot_saved", etc.)
            payload: 이벤트 페이로드
            message_id: 관련 메시지 ID (선택사항)
        
        Returns:
            생성된 이벤트 문서 (dict)
        """
        pass

