# apps/api/utils/request_body.py
"""
Request body 파싱 유틸리티
"""

from typing import Any, Dict
from fastapi import Request


async def safe_json(request: Request) -> Dict[str, Any]:
    """
    Request에서 JSON body를 안전하게 파싱합니다.
    
    content-type이 application/json이 아니면 빈 딕셔너리를 반환합니다.
    파싱 실패 시에도 빈 딕셔너리를 반환하여 500 에러를 방지합니다.
    
    Args:
        request: FastAPI Request 객체
    
    Returns:
        파싱된 JSON 딕셔너리. 파싱 실패 시 빈 딕셔너리 반환
    """
    # content-type이 json이 아니면 파싱 시도 자체를 안 함
    ctype = (request.headers.get("content-type") or "").lower()
    if "application/json" not in ctype:
        return {}
    
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

