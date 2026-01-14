# apps/api/services/logging_service.py
"""
로깅 서비스: access_logs, event_logs, error_logs 저장
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request
from adapters.persistence.mongo import get_db

logger = logging.getLogger(__name__)

# Payload 최대 크기 (8KB)
MAX_PAYLOAD_BYTES = 8192


def get_anon_id(request: Request) -> str:
    """
    Request에서 anon_id를 추출합니다.
    우선순위: X-Anon-Id 헤더 > cookie anon_id > "missing"
    """
    # 헤더에서 먼저 확인
    anon_id = request.headers.get("X-Anon-Id")
    if anon_id:
        return anon_id.strip()
    
    # 쿠키에서 확인
    anon_id = request.cookies.get("anon_id")
    if anon_id:
        return anon_id.strip()
    
    return "missing"


def get_user_id(request: Request) -> Optional[str]:
    """
    Request에서 user_id를 추출합니다.
    request.state.user_id 또는 request.state.current_user에서 가져옵니다.
    """
    # request.state에 user_id가 있는지 확인
    if hasattr(request.state, "user_id") and request.state.user_id:
        return str(request.state.user_id)
    
    # request.state에 current_user가 있는지 확인
    if hasattr(request.state, "current_user") and request.state.current_user:
        user = request.state.current_user
        if isinstance(user, dict):
            return user.get("user_id")
        elif hasattr(user, "user_id"):
            return str(user.user_id)
    
    return None


def get_ip_ua_ref(request: Request) -> Dict[str, Optional[str]]:
    """
    Request에서 IP, User-Agent, Referer를 추출합니다.
    """
    # IP 주소 추출 (프록시 고려)
    ip = request.headers.get("X-Forwarded-For")
    if ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        ip = request.headers.get("X-Real-IP")
    if not ip:
        ip = request.client.host if request.client else None
    
    ua = request.headers.get("User-Agent")
    ref = request.headers.get("Referer")
    
    return {
        "ip": ip,
        "user_agent": ua,
        "referer": ref,
    }


def limit_payload(payload: Any, max_bytes: int = MAX_PAYLOAD_BYTES) -> Dict[str, Any]:
    """
    Payload를 JSON으로 직렬화하여 크기를 확인하고, 초과 시 truncate 처리합니다.
    
    Returns:
        {
            "payload": {...},  # 원본 또는 truncated 버전
            "truncated": bool,
            "original_size": int,
        }
    """
    try:
        payload_str = json.dumps(payload, ensure_ascii=False)
        payload_bytes = len(payload_str.encode("utf-8"))
        
        if payload_bytes <= max_bytes:
            return {
                "payload": payload,
                "truncated": False,
                "original_size": payload_bytes,
            }
        
        # 초과 시 truncate
        # payload가 dict인 경우 일부 필드만 유지
        if isinstance(payload, dict):
            truncated = {
                "truncated": True,
                "original_size": payload_bytes,
                "keys": list(payload.keys())[:10],  # 키 목록만 저장
            }
        else:
            truncated = {
                "truncated": True,
                "original_size": payload_bytes,
                "type": type(payload).__name__,
            }
        
        return {
            "payload": truncated,
            "truncated": True,
            "original_size": payload_bytes,
        }
    except Exception as e:
        logger.warning(f"Failed to limit payload: {e}")
        return {
            "payload": {"error": "payload_serialization_failed"},
            "truncated": False,
            "original_size": 0,
        }


def insert_access_log(doc: Dict[str, Any]) -> None:
    """
    access_logs 컬렉션에 접근 로그를 저장합니다.
    """
    try:
        db = get_db()
        db.access_logs.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to insert access log: {e}", exc_info=True)


def insert_event_log(doc: Dict[str, Any]) -> None:
    """
    event_logs 컬렉션에 이벤트 로그를 저장합니다.
    """
    try:
        db = get_db()
        db.event_logs.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to insert event log: {e}", exc_info=True)


def insert_error_log(doc: Dict[str, Any]) -> None:
    """
    error_logs 컬렉션에 에러 로그를 저장합니다.
    """
    try:
        db = get_db()
        db.error_logs.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to insert error log: {e}", exc_info=True)
