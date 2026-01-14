# apps/api/routes/logs.py
"""
로그 수집 API: event_logs, error_logs
"""

import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from apps.api.services.logging_service import (
    get_anon_id,
    get_user_id,
    get_ip_ua_ref,
    limit_payload,
    insert_event_log,
    insert_error_log,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class EventLogRequest(BaseModel):
    """이벤트 로그 요청"""
    name: str = Field(..., description="이벤트 이름")
    source: str = Field(..., description="이벤트 소스 (character|world|game|ui|auth|token|system)")
    path: Optional[str] = Field(None, description="페이지 경로")
    session_id: Optional[str] = Field(None, description="세션 ID")
    entity_id: Optional[str] = Field(None, description="엔티티 ID (game_id/character_id/world_id)")
    request_id: Optional[str] = Field(None, description="요청 ID (trace_id)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="이벤트 페이로드 (8KB 제한)")


class ErrorLogRequest(BaseModel):
    """에러 로그 요청"""
    kind: str = Field(..., description="에러 종류 (client|server)")
    source: str = Field(..., description="에러 소스 (window.onerror|unhandledrejection|apiFetch)")
    message: str = Field(..., description="에러 메시지")
    stack: Optional[str] = Field(None, description="스택 트레이스")
    path: Optional[str] = Field(None, description="페이지 경로")
    meta: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


@router.post("/event")
async def log_event(request: Request, event_req: EventLogRequest):
    """
    클라이언트에서 발생한 이벤트를 event_logs에 저장합니다.
    """
    try:
        anon_id = get_anon_id(request)
        user_id = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        
        # Payload 크기 제한
        payload_result = limit_payload(event_req.payload)
        
        doc = {
            "ts": datetime.now(timezone.utc),
            "name": event_req.name,
            "source": event_req.source,
            "anon_id": anon_id,
            "user_id": user_id,
            "path": event_req.path,
            "session_id": event_req.session_id,
            "entity_id": event_req.entity_id,
            "request_id": event_req.request_id,
            "payload": payload_result["payload"],
            "payload_truncated": payload_result["truncated"],
            "payload_original_size": payload_result["original_size"],
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
        }
        
        insert_event_log(doc)
        
        return {"ok": True, "saved": True}
    except Exception as e:
        logger.error(f"Failed to log event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log event")


@router.post("/error")
async def log_error(request: Request, error_req: ErrorLogRequest):
    """
    클라이언트에서 발생한 에러를 error_logs에 저장합니다.
    """
    try:
        anon_id = get_anon_id(request)
        user_id = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        
        # Stack 크기 제한 (16KB)
        stack = error_req.stack
        if stack:
            stack_bytes = len(stack.encode("utf-8"))
            if stack_bytes > 16384:
                stack = stack[:16384] + "... [truncated]"
        
        # Meta 크기 제한
        meta_result = limit_payload(error_req.meta, max_bytes=8192)
        
        doc = {
            "ts": datetime.now(timezone.utc),
            "kind": error_req.kind,
            "source": error_req.source,
            "message": error_req.message[:1000],  # 메시지도 1KB로 제한
            "stack": stack,
            "anon_id": anon_id,
            "user_id": user_id,
            "path": error_req.path,
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
            "meta": meta_result["payload"],
            "meta_truncated": meta_result["truncated"],
        }
        
        insert_error_log(doc)
        
        return {"ok": True, "saved": True}
    except Exception as e:
        logger.error(f"Failed to log error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log error")
