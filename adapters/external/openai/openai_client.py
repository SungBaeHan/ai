# adapters/external/openai/openai_client.py
"""
OpenAI API 클라이언트 유틸리티 모듈
"""

from typing import List, Dict, Optional
import os
import time
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# 1) 두 환경변수 모두 지원: 기존 코드와 새 코드 호환
api_key = (
    os.getenv("OPEN_API_KEY")      # 기존 변수명
    or os.getenv("OPENAI_API_KEY")  # 새 변수명
)

# 2) Base URL
base_url = (
    os.getenv("OPENAI_API_BASE")
    or os.getenv("OPENAI_BASE_URL")
    or "https://api.openai.com/v1"
)

# 3) Model
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 4) 디버깅 로그
if not api_key:
    logger.error("❌ No OpenAI API key found. (OPEN_API_KEY / OPENAI_API_KEY both missing)")
else:
    logger.info(
        f"🔑 OpenAI Client Initialized | base={base_url} | model={model_name} | key_len={len(api_key)}"
    )

# OpenAI 클라이언트 인스턴스 생성
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
) if api_key else None

# 호환성을 위한 변수명 유지
OPENAI_API_KEY = api_key
OPENAI_API_BASE = base_url
DEFAULT_MODEL = model_name


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
        model: 사용할 모델명 (기본값: 환경변수 OPENAI_MODEL 또는 "gpt-4o-mini")
        temperature: 생성 온도 (0.0 ~ 2.0, 기본값: 0.7)
        max_tokens: 최대 토큰 수 (기본값: 32)
    
    Returns:
        assistant의 최종 reply 텍스트
    
    Raises:
        ValueError: OPENAI_API_KEY가 설정되지 않은 경우
        Exception: OpenAI API 호출 실패 시
    """
    if not client:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    # max_tokens가 명시되지 않으면 기본값 32 사용
    if max_tokens is None:
        max_tokens = 32
    
    # 실제 사용할 모델명 결정
    actual_model = model or DEFAULT_MODEL
    
    # OpenAI 호출 시간 측정 및 로깅
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=actual_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.perf_counter() - start
    
    logger.info(
        "OpenAI chat completed in %.2fs (model=%s, max_tokens=%s)",
        elapsed,
        actual_model,
        max_tokens,
    )
    
    return response.choices[0].message.content or ""

