# apps/api/utils/trace.py
"""
트레이스 ID 생성 유틸리티
"""

import uuid


def make_trace_id() -> str:
    """
    요청마다 고유한 trace_id를 생성합니다.
    
    Returns:
        "chat-{uuid4의 앞 8자리}" 형식의 문자열
        예: "chat-1a2b3c4d"
    """
    uuid_str = uuid.uuid4().hex
    return f"chat-{uuid_str[:8]}"

