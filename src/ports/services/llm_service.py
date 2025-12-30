# src/ports/services/llm_service.py
"""
LLMService 포트 (인터페이스)
Dependency Inversion Principle을 위한 LLM 서비스 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMService(ABC):
    """LLM 서비스 인터페이스"""
    
    @abstractmethod
    def generate_reply(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """
        메시지 리스트를 받아 LLM 응답을 생성합니다.
        
        Args:
            messages: 메시지 리스트 [{"role": "system"|"user"|"assistant", "content": "..."}]
            context: 추가 컨텍스트 (선택사항)
        
        Returns:
            assistant의 응답 텍스트
        """
        pass

