# apps/api/schemas/chat_v2.py
"""
V2 채팅 API 스키마
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SessionSummary(BaseModel):
    """세션 요약 정보"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id")  # Mongo의 _id를 API에서는 id로
    user_id: str
    chat_type: str
    entity_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    status: Optional[str] = None
    state_version: int = 0


class Message(BaseModel):
    """메시지 모델"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id")  # Mongo의 _id를 API에서는 id로
    session_id: str
    user_id: str
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    created_at: datetime
    request_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ChatEvent(BaseModel):
    """채팅 이벤트 모델"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id")  # Mongo의 _id를 API에서는 id로
    session_id: str
    user_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime
    message_id: Optional[str] = None


class OpenChatResponse(BaseModel):
    """채팅 열기 응답"""
    session: Optional[SessionSummary] = None
    messages: List[Message] = []


class SendMessageRequest(BaseModel):
    """메시지 전송 요청"""
    content: str = Field(..., min_length=1)
    request_id: Optional[str] = None


class SendMessageResponse(BaseModel):
    """메시지 전송 응답"""
    session: Dict[str, Any]
    messages: List[Message]

