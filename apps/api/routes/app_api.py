# apps/api/routes/app_api.py
from fastapi import APIRouter, Query
from apps.api.routes.ask import answer  # 경로 보정

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("")
def ask_get(q: str = Query(..., description="질문")):
    q = (q or "").strip()
    if not q:
        return {"answer": ""}
    return {"answer": answer(q)}
