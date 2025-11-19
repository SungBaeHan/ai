# apps/api/main.py
from apps.api import bootstrap  # noqa: F401  (sets env early)
import os, pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apps.api.startup import init_mongo_indexes
from apps.api.routes import health
from apps.api.routes import debug
from apps.api.config import settings

# === 환경값 ===
ROOT = pathlib.Path(__file__).resolve().parents[2]        # 프로젝트 루트 추정
JSON_DIR = ROOT / "data" / "json"
ASSETS_DIR = ROOT / "assets"

# === FastAPI 인스턴스 ===
app = FastAPI(title="TRPG API", version="1.0.0")

app.include_router(health.router)
app.include_router(debug.router, prefix="/v1")

# === API 라우터 등록 (정적 파일 마운트 전에 등록) ===
from apps.api.routes import assets
app.include_router(assets.router)  # /assets/images 라우터를 먼저 등록

# === CORS 설정 ===
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://arcanaverse.pages.dev",
    "https://app.arcanaverse.ai",
    "https://arcanaverse.ai",
    "https://api.arcanaverse.ai"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 정적 파일 마운트 ===
# 주의: /assets/images는 API 라우터가 처리하므로, /assets 경로에 정적 파일을 마운트하지 않음
# 정적 파일은 nginx에서 직접 서빙하거나, 필요시 /static 경로를 사용
# assets_path = os.path.join(os.path.dirname(__file__), "../../apps/web-html/assets")
# 정적 파일 마운트 제거: /assets/images 라우터와 충돌 방지
print(f"[INFO] Static files should be served via nginx, not FastAPI /assets mount")

if ASSETS_DIR.is_dir():
    print(f"[INFO] Assets directory exists: {ASSETS_DIR} (served via API or nginx)")
if JSON_DIR.is_dir():
    app.mount("/json", StaticFiles(directory=str(JSON_DIR)), name="json")  # 홈/챗 폴백 JSON용

# === SQLite 초기화 (조건부) ===
# SQLite를 사용하는 경우에만 초기화
if settings.is_sqlite:
    try:
        from adapters.persistence.sqlite import init_db as init_sqlite
        init_sqlite()
        print("[INFO] SQLite database initialized")
    except Exception as e:
        print(f"[WARN] SQLite initialization failed: {e}")

# === 라우터 등록 ===
from apps.api.routes import characters                 # 캐릭터 API
from apps.api.routes import chat as chat_router    # /v1/chat
from apps.api.routes import ask as ask_router      # /v1/ask
from apps.api.routes import auth as auth_router    # /v1/auth
from apps.api.routes import auth_google            # /v1/auth/google
from apps.api.routes import debug_db
from apps.api.routes import migrate

app.include_router(characters.router, prefix="/v1/characters", tags=["characters"])
app.include_router(chat_router.router,   prefix="/v1/chat",        tags=["chat"])
app.include_router(ask_router.router,    prefix="/v1/ask",         tags=["ask"])
app.include_router(auth_router.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(auth_google.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(debug_db.router)
app.include_router(migrate.router)

# === Repository factory ===
from adapters.persistence.mongo.factory import create_character_repository
repo = create_character_repository()

# === Startup Hook ===
@app.on_event("startup")
async def _on_startup():
    try:
        init_mongo_indexes()
    except Exception:
        # don't crash app on index errors
        pass

# === 루트 경로 ===
@app.get("/")
def root():
    return {"message": "TRPG AI API", "version": "1.0.0", "docs": "/docs"}

# === 헬스체크 ===
@app.get("/health")
def health():
    return {"ok": True}
