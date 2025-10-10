# apps/api/routes/ask.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm  # (필요시 사용)
from langchain_ollama import OllamaLLM
from packages.rag.embedder import embed  # ✅ 경로 보정

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("COLLECTION", "my_docs")

def search(query: str, k=5):
    qvec = embed([query])[0]
    client = QdrantClient(url=QDRANT_URL)
    res = client.query_points(
        collection_name=COLLECTION,
        query=qvec,
        limit=k,
        with_payload=True
    )
    return [p.payload.get("text", "") for p in res.points]

def answer(query: str):
    ctx = "\n\n".join(search(query))
    prompt = f"""아래 자료만 근거로 간결히 한국어로 답해줘.

[자료]
{ctx}

[질문]
{query}
"""
    llm = OllamaLLM(model="llama3.1")
    return llm.invoke(prompt)
