# src/usecases/rag/answer_question.py
"""
RAG 질문 응답 유즈케이스
"""

import os
from typing import Optional
from qdrant_client import QdrantClient
from src.ports.services.embedding_service import EmbeddingService
from adapters.external.llm_client import get_default_llm_client


class AnswerQuestionUseCase:
    """질문 응답 유즈케이스 (RAG + LLM)"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection = os.getenv("COLLECTION", "my_docs")
        
        self.sys_qa = """너는 유능한 도우미다. 답변은 간결하고 정확하게 한국어로 작성한다.
가능하면 근거(컨텍스트)를 자연스럽게 녹여 설명한다.
모르겠으면 모른다고 말하고, 추측하지 않는다.
"""
    
    def _retrieve_context(self, query: str, k: int = 5) -> str:
        """RAG를 위한 컨텍스트 검색"""
        try:
            qvec = self.embedding_service.embed([query])[0]
            cli = QdrantClient(url=self.qdrant_url)
            res = cli.query_points(
                collection_name=self.collection,
                query=qvec,
                limit=k,
                with_payload=True
            )
            chunks = []
            for p in getattr(res, "points", []):
                payload = getattr(p, "payload", {}) or {}
                txt = payload.get("text", "")
                if txt:
                    chunks.append(txt)
            return "\n\n".join(chunks)
        except Exception as e:
            print(f"[WARN] retrieve_context error: {e}")
            return ""
    
    def execute(self, question: str) -> str:
        """질문에 대한 답변 생성"""
        if not question or not question.strip():
            return ""
        
        context = self._retrieve_context(question)
        sys_prompt = self.sys_qa
        if context:
            sys_prompt += f"\n[검색 컨텍스트]\n{context}\n"
        
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question}
        ]
        
        try:
            llm_client = get_default_llm_client()
            response = llm_client.generate_chat_completion(
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                timeout=120,
            )
            return response.strip() if response else ""
        except Exception as e:
            print(f"[WARN] answer error: {e}")
            return f"(오류 발생) {e}"
