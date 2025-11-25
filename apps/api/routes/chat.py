# apps/api/routes/chat.py

import logging

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def chat(req: ChatRequest):
    """
    테스트용 /v1/chat 엔드포인트.
    - ollama, qdrant 등은 전혀 호출하지 않고,
      바로 짧은 JSON 응답을 돌려준다.
    """
    logger.info("TEST /v1/chat called. message=%r", req.message)
    # 일부러 약간의 정보와 함께 200 응답
    return {
        "answer": f"[TEST OK] 서버에서 '{req.message}' 를 잘 받았습니다.",
        "ok": True,
    }


@router.get("/health")
def health():
    return {"status": "ok", "endpoint": "/v1/chat/"}
