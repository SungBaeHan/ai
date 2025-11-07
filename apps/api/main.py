# apps/api/main.py
import os, sqlite3, pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# === 환경값 ===
ROOT = pathlib.Path(__file__).resolve().parents[2]        # 프로젝트 루트 추정
DB_PATH = os.getenv("DB_PATH", str(ROOT / "data" / "db" / "app.sqlite3"))
JSON_DIR = ROOT / "data" / "json"
ASSETS_DIR = ROOT / "assets"

# === FastAPI 인스턴스 ===
app = FastAPI(title="TRPG API", version="1.0.0")

# === CORS 설정 ===
origins = [
    "https://arcanaverse.pages.dev",
    "https://app.arcanaverse.ai"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 정적 파일 마운트 ===
if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
if JSON_DIR.is_dir():
    app.mount("/json", StaticFiles(directory=str(JSON_DIR)), name="json")  # 홈/챗 폴백 JSON용

# === SQLite 초기 설정 (WAL + busy_timeout) : 다중 접근 대비 ===
def _tune_sqlite():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")          # 동시성 ↑
        conn.execute("PRAGMA synchronous=NORMAL")        # 안정/성능 균형
        conn.execute("PRAGMA busy_timeout=8000")         # 잠금 대기 여유
        conn.close()
    except Exception as e:
        print(f"[WARN] sqlite tune failed: {e}")

_tune_sqlite()

# === 라우터 등록 ===
from apps.api.routes import characters                 # 캐릭터 API
from apps.api.routes import chat as chat_router    # /v1/chat
from apps.api.routes import ask as ask_router      # /v1/ask
from apps.api.routes import auth as auth_router    # /v1/auth
from apps.api.routes import auth_google            # /v1/auth/google
from apps.api.routes import assets
from apps.api.routes import debug_db
from apps.api.routes import migrate

app.include_router(characters.router, prefix="/v1/characters", tags=["characters"])
app.include_router(chat_router.router,   prefix="/v1/chat",        tags=["chat"])
app.include_router(ask_router.router,    prefix="/v1/ask",         tags=["ask"])
app.include_router(auth_router.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(auth_google.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(assets.router)
app.include_router(debug_db.router)
app.include_router(migrate.router)

# === 루트 경로 ===
@app.get("/")
def root():
    return {"message": "TRPG AI API", "version": "1.0.0", "docs": "/docs"}

# === 헬스체크 ===
@app.get("/health")
def health():
    return {"ok": True}
