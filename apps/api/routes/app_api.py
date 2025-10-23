# ========================================
# apps/api/routes/app_api.py — 주석 추가 상세 버전
# /v1/ask 엔드포인트: 간단 질의응답 API. 내부적으로 ask.answer() 호출.
# ========================================

from fastapi import APIRouter, Query           # 라우터 및 쿼리 파라미터 유효성 검사용
from apps.api.routes.ask import answer         # 실제 RAG+LLM 답변 함수를 임포트

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
