# apps/api/routes/chat_v2.py
"""
V2 채팅 API 라우터
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from bson import ObjectId

from apps.api.routes.worlds import get_current_user_v2
from apps.api.schemas.chat_v2 import (
    OpenChatResponse,
    SendMessageRequest,
    SendMessageResponse,
    Message,
    SessionSummary,
)
from src.ports.repositories.chat_repository import ChatRepository
from src.ports.services.llm_service import LLMService
from src.usecases.chat.open_chat import OpenChatUseCase
from src.usecases.chat.send_message import SendMessageUseCase
from adapters.persistence.mongo.chat_repository_adapter import MongoChatRepository
from adapters.external.llm_service_adapter import LLMServiceAdapter

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chat_repository() -> ChatRepository:
    """ChatRepository 인스턴스 생성"""
    return MongoChatRepository()


def get_llm_service() -> LLMService:
    """LLMService 인스턴스 생성"""
    return LLMServiceAdapter()


@router.get("/{chat_type}/{entity_id}", response_model=OpenChatResponse, summary="채팅 열기")
async def open_chat(
    chat_type: str,
    entity_id: str,
    request: Request,
    limit: int = 100,
    repository: ChatRepository = Depends(get_chat_repository),
):
    """
    채팅 세션을 열고 메시지 목록을 조회합니다.
    
    Args:
        chat_type: 채팅 타입 ("character" | "world" | "game")
        entity_id: 엔티티 ID
        limit: 최대 메시지 개수
        current_user: 현재 사용자 정보 (의존성 주입)
        repository: ChatRepository (의존성 주입)
    
    Returns:
        OpenChatResponse: 세션 및 메시지 목록
    """
    # 인증 체크
    current_user = get_current_user_v2(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    user_id = current_user.get("google_id") or current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
    
    # chat_type 검증
    if chat_type not in ["character", "world", "game"]:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 chat_type: {chat_type}")
    
    # 유스케이스 실행
    usecase = OpenChatUseCase(repository=repository)
    result = usecase.execute(
        user_id=str(user_id),
        chat_type=chat_type,
        entity_id=entity_id,
        limit=limit,
    )
    
    # 응답 변환
    session_summary = None
    if result["session"]:
        session_summary = SessionSummary(**result["session"])
    
    messages = [Message(**msg) for msg in result["messages"]]
    
    return OpenChatResponse(
        session=session_summary,
        messages=messages,
    )


@router.post("/{chat_type}/{entity_id}/messages", response_model=SendMessageResponse, summary="메시지 전송")
async def send_message(
    chat_type: str,
    entity_id: str,
    payload: SendMessageRequest,
    request: Request,
    repository: ChatRepository = Depends(get_chat_repository),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    메시지를 전송하고 LLM 응답을 생성합니다.
    
    Args:
        chat_type: 채팅 타입 ("character" | "world" | "game")
        entity_id: 엔티티 ID
        payload: 메시지 전송 요청
        current_user: 현재 사용자 정보 (의존성 주입)
        repository: ChatRepository (의존성 주입)
        llm_service: LLMService (의존성 주입)
    
    Returns:
        SendMessageResponse: 업데이트된 세션 및 생성된 메시지 리스트
    """
    # 인증 체크
    current_user = get_current_user_v2(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    user_id = current_user.get("google_id") or current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
    
    # chat_type 검증
    if chat_type not in ["character", "world", "game"]:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 chat_type: {chat_type}")
    
    # 유스케이스 실행
    usecase = SendMessageUseCase(repository=repository, llm_service=llm_service)
    result = usecase.execute(
        user_id=str(user_id),
        chat_type=chat_type,
        entity_id=entity_id,
        content=payload.content,
        request_id=payload.request_id,
    )
    
    # 응답 변환
    messages = [Message(**msg) for msg in result["messages"]]
    
    return SendMessageResponse(
        session=result["session"],
        messages=messages,
    )

