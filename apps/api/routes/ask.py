# ========================================
# apps/api/routes/ask.py — 주석 추가 상세 버전
# RAG 검색(Qdrant) + Ollama LLM으로 간단 질의응답을 수행하는 모듈.
# app_api.py에서 import하여 /v1/ask 엔드포인트에 사용된다.
# ========================================

import os                                       # 환경변수에서 Qdrant URL, 콜렉션 이름을 읽기 위함
from qdrant_client import QdrantClient          # Qdrant 서버 클라이언트
from qdrant_client.http import models as qm      # (필요 시) Qdrant HTTP 모델
from langchain_ollama import OllamaLLM          # Ollama LLM(프롬프트 문자열 입력형)
from packages.rag.embedder import embed         # 텍스트 임베딩 함수 (벡터 생성)

# Qdrant 접속 정보: 환경변수 없으면 기본 로컬 사용
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("COLLECTION", "my_docs")

def search(query: str, k=5):
    """질문(query)을 임베딩하여 Qdrant에서 상위 k개 유사 문서를 가져온다."""
    qvec = embed([query])[0]                    # 질문을 벡터로 변환(첫번째 결과 사용)
    client = QdrantClient(url=QDRANT_URL)       # Qdrant 클라이언트 생성
    res = client.query_points(                  # 벡터 질의 실행
        collection_name=COLLECTION,             # 검색할 콜렉션 이름
        query=qvec,                             # 질의 벡터
        limit=k,                                # 상위 k개
        with_payload=True                       # payload(원문 텍스트 등) 포함
    )
    # 결과에서 payload의 "text"만 추출하여 리스트로 반환
    return [p.payload.get("text", "") for p in res.points]

def answer(query: str):
    """검색 결과를 컨텍스트로 사용하여 LLM으로 최종 답변을 생성한다."""
    ctx = "\n\n".join(search(query))            # 상위 문서들을 하나의 컨텍스트 문자열로 합침
    prompt = f"""아래 자료만 근거로 간결히 한국어로 답해줘.

[자료]
{ctx}

[질문]
{query}
"""
    # Ollama LLM 인스턴스(단순 문자열 prompt 입력)
    llm = OllamaLLM(model="llama3.1")
    return llm.invoke(prompt)                   # 모델 호출 결과 문자열 반환
