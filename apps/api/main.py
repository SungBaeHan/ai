# ========================================
# apps/api/main.py — FastAPI 엔트리 포인트
# - /assets 정적 경로 마운트
# - /  → home.html
# - /chat → chat.html
# - /v1/* 라우터 조립
# ========================================

import os                                               # 표준 라이브러리 (경로 계산)
from fastapi import FastAPI                             # FastAPI 앱 본체
from fastapi.middleware.cors import CORSMiddleware      # 개발 편의 CORS 허용
from fastapi.staticfiles import StaticFiles             # 정적 파일 제공
from fastapi.responses import FileResponse, PlainTextResponse  # HTML 파일 응답

# 기능별 라우터들
from apps.api.routes import app_chat, app_api, characters  # /v1/chat, /v1/ask, /v1/characters

# FastAPI 인스턴스 (문서 타이틀/버전)
app = FastAPI(
    title="AI TRPG MVP API",
    version="2.0.0",
    description="LangChain + Qdrant + Ollama 기반 TRPG API",
)

# ---- CORS(개발시 전부 허용; 운영에서는 도메인 제한 권장) -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 모든 origin 허용
    allow_credentials=True,         # 쿠키 등 인증정보 허용
    allow_methods=["*"],            # 모든 메서드 허용
    allow_headers=["*"],            # 모든 헤더 허용
)

# ---- 경로 상수 (프로젝트 구조 기준 계산) ---------------------------------------
APPS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/
ROOT_DIR = os.path.dirname(APPS_DIR)                                     # 프로젝트 루트
WEB_DIR  = os.path.join(APPS_DIR, "web-html")                            # 정적/HTML 폴더
ASSETS_DIR = os.path.join(WEB_DIR, "assets")                             # /assets 실제 폴더

# ---- 정적 자원 마운트 ---------------------------------------------------------
# 반드시 /assets 가 apps/web-html/assets 로 매핑되어야 이미지가 보임
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# ---- HTML 페이지 라우트 -------------------------------------------------------
def file_or_hint(path: str, hint: str):
    """파일이 있으면 FileResponse, 없으면 안내문(PlainText) 반환."""
    if os.path.isfile(path):
        return FileResponse(path)
    return PlainTextResponse(
        f"{hint}\n(없음: {path})",
        status_code=200,
        media_type="text/plain; charset=utf-8",
    )

@app.get("/")
def home_page():
    path = os.path.join(WEB_DIR, "home.html")
    return FileResponse(path, headers={"Cache-Control": "no-store"})

@app.get("/chat")
def chat_page():
    path = os.path.join(WEB_DIR, "chat.html")
    # 캐시가 붙으면 예전 파일이 계속 열려 스크립트가 안 바뀐 것처럼 보입니다.
    return FileResponse(path, headers={"Cache-Control": "no-store"})

# ---- API 라우터 조립 ---------------------------------------------------------
app.include_router(app_chat.router,     prefix="/v1/chat",        tags=["Chat"])        # LLM 호출
app.include_router(app_api.router,      prefix="/v1/ask",         tags=["Ask"])         # 단문 Q&A
app.include_router(characters.router,   prefix="/v1/characters",  tags=["Characters"])  # 캐릭터 목록/상세

@app.get("/healthz")
def healthz():
    """헬스체크 엔드포인트"""
    return {"status": "ok"}

# ---- 단독 실행시 uvicorn 구동 -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
