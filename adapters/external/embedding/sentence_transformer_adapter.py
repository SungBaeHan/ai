# adapters/external/embedding/sentence_transformer_adapter.py
"""
SentenceTransformer EmbeddingService 어댑터
기존 adapters.external.embedding.sentence_transformer 함수를 래핑하여 포트 인터페이스 구현
"""

from typing import List
from src.ports.services.embedding_service import EmbeddingService
from adapters.external.embedding.sentence_transformer import embed as embed_raw


class SentenceTransformerEmbeddingService(EmbeddingService):
    """SentenceTransformer 구현체"""
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 벡터 임베딩으로 변환"""
        return embed_raw(texts)
