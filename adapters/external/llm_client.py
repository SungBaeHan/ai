# adapters/external/llm_client.py
"""
LLM 클라이언트 공통 인터페이스 및 팩토리
환경변수 LLM_PROVIDER에 따라 OpenAI 또는 Ollama를 선택적으로 사용
"""

from typing import List, Dict, Optional
import os
from apps.api.config import settings


class LLMClient:
    """LLM 클라이언트 공통 인터페이스"""
    
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        메시지 리스트를 받아 LLM 응답을 생성합니다.
        
        Args:
            messages: 메시지 리스트 [{"role": "system"|"user"|"assistant", "content": "..."}]
            model: 사용할 모델명
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터 (provider별로 다를 수 있음)
        
        Returns:
            assistant의 최종 reply 텍스트
        """
        raise NotImplementedError


class OpenAILLMClient(LLMClient):
    """OpenAI 클라이언트 구현"""
    
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        from adapters.external.openai import generate_chat_completion as openai_generate
        
        return openai_generate(
            messages=messages,
            model=model or settings.openai_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )


class OllamaLLMClient(LLMClient):
    """Ollama 클라이언트 구현"""
    
    def __init__(self):
        self.ollama_base = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "trpg-gen")
    
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            base_url=self.ollama_base,
            model=model or self.default_model,
            timeout=kwargs.get("timeout", 120),
            temperature=temperature,
            top_p=kwargs.get("top_p", 0.9),
        )
        
        try:
            raw = llm.invoke(messages)
            text = getattr(raw, "content", str(raw))
            return text.strip() if text else ""
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                model_name = model or self.default_model
                error_msg = f"모델 '{model_name}'이 Ollama에 설치되어 있지 않습니다. Ollama 컨테이너에서 'ollama pull {model_name}' 명령을 실행해주세요."
            print(f"[WARN] Ollama LLM error: {error_msg}")
            raise


def get_llm_client() -> LLMClient:
    """
    환경변수 LLM_PROVIDER에 따라 적절한 LLM 클라이언트를 반환합니다.
    
    Returns:
        LLMClient 인스턴스 (OpenAI 또는 Ollama)
    
    Raises:
        ValueError: 지원하지 않는 provider인 경우
    """
    provider = settings.llm_provider
    
    if provider == "openai":
        return OpenAILLMClient()
    elif provider == "ollama":
        return OllamaLLMClient()
    else:
        raise ValueError(f"지원하지 않는 LLM provider: {provider}. 'openai' 또는 'ollama'를 사용해주세요.")


# 전역 LLM 클라이언트 인스턴스 (지연 초기화)
_llm_client: Optional[LLMClient] = None


def get_default_llm_client() -> LLMClient:
    """전역 LLM 클라이언트 인스턴스를 반환합니다 (싱글톤 패턴)"""
    global _llm_client
    if _llm_client is None:
        _llm_client = get_llm_client()
    return _llm_client

