# apps/api/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

# 라우터
from apps.api.routes import app_chat, app_api

app = FastAPI(
    title="AI TRPG MVP API",
    version="2.0.0",
    description="LangChain + RAG + Redis + Mongo + Qdrant 기반 API",
)

# ------------------------------
# CORS (개발 단계는 전체 허용; 운영 시 도메인 제한)
# ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# 경로 설정
# ------------------------------
# 현재 파일: apps/api/main.py
APPS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../apps
ROOT_DIR = os.path.dirname(APPS_DIR)                                     # 프로젝트 루트
WEB_DIR  = os.path.join(APPS_DIR, "web-html")                            # .../apps/web-html

ASSETS_DIR     = os.path.join(WEB_DIR, "assets")                         # 정적 리소스
JSON_DIR_WEB   = os.path.join(WEB_DIR, "json")                           # 웹 정적 JSON
JSON_DIR_DATA  = os.path.join(ROOT_DIR, "data", "json")                  # data/json (대안)

def safe_mount(url_path: str, dir_path: str, name: str):
    """디렉토리가 존재할 때만 마운트(미존재시 런타임 에러 방지)."""
    if os.path.isdir(dir_path):
        app.mount(url_path, StaticFiles(directory=dir_path), name=name)
    else:
        print(f"[WARN] skip mount {url_path} -> {dir_path} (not found)")

# 정적 폴더 마운트
safe_mount("/assets", ASSETS_DIR,   "assets")
# /json 은 웹 폴더가 우선, 없으면 data/json 사용
if os.path.isdir(JSON_DIR_WEB):
    safe_mount("/json", JSON_DIR_WEB, "json-web")
elif os.path.isdir(JSON_DIR_DATA):
    safe_mount("/json", JSON_DIR_DATA, "json-data")
else:
    print("[WARN] no JSON directory found for /json")

# ------------------------------
# HTML 라우트
# ------------------------------
def file_or_hint(path: str, hint: str):
    """파일이 있으면 FileResponse, 없으면 간단 안내."""
    if os.path.isfile(path):
        return FileResponse(path)
    return PlainTextResponse(
        f"{hint}\n(찾는 파일이 없습니다: {path})",
        status_code=200,
        media_type="text/plain; charset=utf-8",
    )

@app.get("/")
def home_page():
    return file_or_hint(
        os.path.join(WEB_DIR, "home.html"),
        "홈 페이지가 아직 없어요. apps/web-html/home.html 을 추가하세요.",
    )

@app.get("/chat")
def chat_page():
    return file_or_hint(
        os.path.join(WEB_DIR, "chat.html"),
        "채팅 페이지가 아직 없어요. apps/web-html/chat.html 을 추가하세요.",
    )

# ------------------------------
# API 라우터 조립
# ------------------------------
app.include_router(app_chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(app_api.router,  prefix="/v1/ask",  tags=["Ask"])

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# ------------------------------
# 로컬 실행
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
