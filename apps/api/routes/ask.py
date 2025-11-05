# ========================================
# apps/api/routes/ask.py — 주석 추가 상세 버전
# /v1/ask 엔드포인트: 간단 질의응답 API. 내부적으로 ask.answer() 호출.
# ========================================

import os
from fastapi import APIRouter, Query           # 라우터 및 쿼리 파라미터 유효성 검사용
from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from adapters.external.embedding.sentence_transformer import embed

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("COLLECTION", "my_docs")
OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "trpg-gen")

SYS_QA = """너는 유능한 도우미다. 답변은 간결하고 정확하게 한국어로 작성한다.
가능하면 근거(컨텍스트)를 자연스럽게 녹여 설명한다.
모르겠으면 모른다고 말하고, 추측하지 않는다.
"""

def retrieve_context(query: str, k: int = 5) -> str:
    """RAG를 위한 컨텍스트 검색"""
    try:
        qvec = embed([query])[0]
        cli = QdrantClient(url=QDRANT_URL)
        res = cli.query_points(collection_name=COLLECTION, query=qvec, limit=k, with_payload=True)
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

def answer(q: str) -> str:
    """질문에 대한 답변 생성 (RAG + LLM)"""
    if not q or not q.strip():
        return ""
    
    context = retrieve_context(q)
    sys_prompt = SYS_QA
    if context:
        sys_prompt += f"\n[검색 컨텍스트]\n{context}\n"
    
    llm = ChatOllama(
        base_url=OLLAMA_BASE,
        model=DEFAULT_MODEL,
        timeout=120,
        temperature=0.7,
        top_p=0.9,
    )
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": q}
    ]
    
    try:
        raw = llm.invoke(messages)
        text = getattr(raw, "content", str(raw))
        return text.strip() if text else ""
    except Exception as e:
        print(f"[WARN] answer error: {e}")
        return f"(오류 발생) {e}"

# 라우터 인스턴스 생성
router = APIRouter()

@router.get("/health")
def health():
    """간단 상태 확인용 엔드포인트: /v1/ask/health"""
    return {"status": "ok"}                    # 정상 작동 신호

@router.get("")
def ask_get(q: str = Query(..., description="질문")):
    """GET /v1/ask?q=... 형태로 질문을 받아 answer()에 위임한다."""
    q = (q or "").strip()                      # 공백/None 방지
    if not q:                                  # 빈 질문이면
        return {"answer": ""}                  # 빈 답변 반환
    return {"answer": answer(q)}               # 핵심 로직 위임
