# adapters/external/openai/openai_client.py
"""
OpenAI API 클라이언트 유틸리티 모듈
"""

from typing import List, Dict, Optional
import os
from openai import OpenAI

# 환경변수에서 설정 읽기
OPEN_API_KEY = os.getenv("OPEN_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# OpenAI 클라이언트 인스턴스 생성
client = OpenAI(
    api_key=OPEN_API_KEY,
    base_url=OPENAI_API_BASE,
) if OPEN_API_KEY else None


def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    OpenAI Chat Completion API를 호출하여 응답을 생성합니다.
    
    Args:
        messages: 메시지 리스트 [{"role": "system"|"user"|"assistant", "content": "..."}]
        model: 사용할 모델명 (기본값: 환경변수 OPENAI_MODEL 또는 "gpt-4.1-mini")
        temperature: 생성 온도 (0.0 ~ 2.0, 기본값: 0.7)
        max_tokens: 최대 토큰 수 (기본값: None, 모델 기본값 사용)
    
    Returns:
        assistant의 최종 reply 텍스트
    
    Raises:
        ValueError: OPEN_API_KEY가 설정되지 않은 경우
        Exception: OpenAI API 호출 실패 시
    """
    if not client:
        raise ValueError("OPEN_API_KEY 환경변수가 설정되지 않았습니다.")
    
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return response.choices[0].message.content or ""

