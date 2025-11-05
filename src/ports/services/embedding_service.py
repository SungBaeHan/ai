# src/ports/services/embedding_service.py
"""
EmbeddingService 포트 (인터페이스)
Dependency Inversion Principle을 위한 임베딩 서비스 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """임베딩 서비스 인터페이스"""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 벡터 임베딩으로 변환"""
        pass
