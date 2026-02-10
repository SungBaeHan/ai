# apps/api/main.py
from apps.api import bootstrap  # noqa: F401  (sets env early)
import os
import logging
import pathlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from apps.api.startup import init_mongo_indexes
from apps.api.routes import health
from apps.api.routes import debug
from apps.api.config import settings

logger = logging.getLogger(__name__)

# === 환경값 ===
ROOT = pathlib.Path(__file__).resolve().parents[2]        # 프로젝트 루트 추정
JSON_DIR = ROOT / "data" / "json"
ASSETS_DIR = ROOT / "assets"

# === FastAPI 인스턴스 ===
app = FastAPI(title="TRPG API", version="1.0.0")

# ✅ 허용할 Origin 목록 (로컬 + 배포)
ALLOWED_ORIGINS = [
    # 로컬 개발
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # 프로덕션 도메인 (Cloudflare Pages)
    "https://arcanaverse.ai",
    "https://www.arcanaverse.ai",
]

logger.info("CORS ALLOWED_ORIGINS: %s", ALLOWED_ORIGINS)

# 👉 커스텀 미들웨어는 제거하고, FastAPI CORSMiddleware 하나만 사용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,          # 쿠키/인증정보 허용
    allow_methods=["*"],             # 모든 메서드 허용
    allow_headers=[
        "Authorization",
        "X-Access-Token",
        "X-Authorization",
        "X-User-Info-Token",
        "X-Anon-Id",  # anon_id 헤더 추가
        "Content-Type",
        "*",  # 모든 헤더 허용 (하위 호환)
    ],
    expose_headers=["*"],
    max_age=3600,
)

# === Access Log 미들웨어 ===
from datetime import datetime, timezone
from apps.api.services.logging_service import (
    get_anon_id,
    get_user_id,
    get_ip_ua_ref,
    insert_access_log,
)
from apps.api.utils.trace import make_trace_id
import time

@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    """
    모든 API 요청/응답을 access_logs에 기록합니다.
    정적 파일 및 health 체크는 제외합니다.
    """
    # 제외할 경로 확인
    path = request.url.path
    excluded_paths = ["/assets", "/json", "/js", "/static", "/health"]
    excluded_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg", ".gif"]
    
    # 제외 경로 체크
    should_log = True
    if any(path.startswith(excluded) for excluded in excluded_paths):
        should_log = False
    elif any(path.lower().endswith(ext) for ext in excluded_extensions):
        should_log = False
    
    if not should_log:
        return await call_next(request)
    
    # 요청 시작 시간
    start_time = time.time()
    
    # Trace ID 생성 (요청마다 고유)
    trace_id = make_trace_id()
    request.state.trace_id = trace_id
    
    # 요청 정보 수집
    anon_id = get_anon_id(request)
    user_id = get_user_id(request)
    ip_ua_ref = get_ip_ua_ref(request)
    
    # Query 파라미터 (민감정보 제외)
    query_dict = {}
    try:
        for key, value in request.query_params.items():
            # password, token, secret 등 민감 키는 제외
            if any(sensitive in key.lower() for sensitive in ["password", "token", "secret", "key"]):
                query_dict[key] = "[REDACTED]"
            else:
                query_dict[key] = value
    except Exception:
        query_dict = {}
    
    # 응답 처리
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise
    finally:
        # 응답 시간 계산
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Access log 문서 생성
        doc = {
            "ts": datetime.now(timezone.utc),
            "method": request.method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "anon_id": anon_id,
            "user_id": user_id,
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
            "query": query_dict if query_dict else None,
            "trace_id": trace_id,
        }
        
        # 비동기로 저장 (응답 지연 최소화)
        try:
            insert_access_log(doc)
        except Exception as e:
            logger.warning(f"Failed to insert access log: {e}")
    
    return response

app.include_router(health.router)
app.include_router(debug.router, prefix="/v1")

# === API 라우터 등록 (정적 파일 마운트 전에 등록) ===
from apps.api.routes import assets
app.include_router(assets.router)  # /assets/images 라우터를 먼저 등록


# === 정적 파일 마운트 ===
# /assets/images는 API 라우터가 처리하므로, /assets 전체를 마운트하지 않음
# /assets/persona/ 경로만 별도로 마운트 (API 라우터보다 구체적이므로 우선순위 높음)
if ASSETS_DIR.is_dir():
    persona_dir = ASSETS_DIR / "persona"
    if persona_dir.is_dir():
        app.mount("/assets/persona", StaticFiles(directory=str(persona_dir)), name="persona-assets")
        logger.info(f"[INFO] Mounted /assets/persona from {persona_dir}")
    else:
        logger.warning(f"[CHAT][PERSONA] trace=startup persona_missing path={persona_dir}")
    logger.info(f"[INFO] Assets directory exists: {ASSETS_DIR}")
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
from apps.api.routes import worlds                     # 세계관 API
from apps.api.routes import games                      # 게임 API
from apps.api.routes import game_turn                  # 게임 턴 API
from apps.api.routes import app_chat as chat_router    # /v1/chat (TRPG LLM)
from apps.api.routes import ask as ask_router      # /v1/ask
from apps.api.routes import auth as auth_router    # /v1/auth
from apps.api.routes import auth_google            # /v1/auth/google
from apps.api.routes import debug_db
from apps.api.routes import migrate
from apps.api.routes.user import router as user_router
from apps.api.routes import personas
from apps.api.routes import chat_v2
from apps.api.routes import character_sessions
from apps.api.routes import world_sessions
from apps.api.routes import logs

app.include_router(characters.router, prefix="/v1/characters", tags=["characters"])
app.include_router(character_sessions.router, prefix="/v1/character-sessions", tags=["character-sessions"])
app.include_router(worlds.router, prefix="/v1/worlds", tags=["worlds"])
app.include_router(world_sessions.router, prefix="/v1/world-sessions", tags=["world-sessions"])
app.include_router(games.router, prefix="/v1/games", tags=["games"])
app.include_router(game_turn.router, prefix="/v1/games", tags=["games"])
app.include_router(chat_router.router,   prefix="/v1/chat",        tags=["chat"])
app.include_router(ask_router.router,    prefix="/v1/ask",         tags=["ask"])
app.include_router(auth_router.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(auth_google.router,   prefix="/v1/auth",        tags=["auth"])
app.include_router(user_router, prefix="/v1")
app.include_router(personas.router, prefix="/v1")
app.include_router(chat_v2.router, prefix="/chat/v2", tags=["chat_v2"])
app.include_router(logs.router, prefix="/v1/logs", tags=["logs"])
app.include_router(debug_db.router)
app.include_router(migrate.router)

# === Repository factory ===
from adapters.persistence.mongo.factory import create_character_repository
repo = create_character_repository()

# === 예외 핸들러 ===
from apps.api.services.logging_service import insert_error_log
from datetime import datetime, timezone
import traceback

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    # Error log 기록
    try:
        anon_id = get_anon_id(request)
        user_id = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        trace_id = getattr(request.state, "trace_id", None)
        
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if len(stack.encode("utf-8")) > 16384:
            stack = stack[:16384] + "... [truncated]"
        
        error_doc = {
            "ts": datetime.now(timezone.utc),
            "kind": "server",
            "error_type": "FastAPIHTTPException",
            "message": str(exc.detail)[:1000],
            "stack": stack,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "anon_id": anon_id,
            "user_id": user_id,
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
            "trace_id": trace_id,
        }
        insert_error_log(error_doc)
    except Exception as e:
        logger.warning(f"Failed to log error in exception handler: {e}")
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    return response

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    # Error log 기록
    try:
        anon_id = get_anon_id(request)
        user_id = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        trace_id = getattr(request.state, "trace_id", None)
        
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if len(stack.encode("utf-8")) > 16384:
            stack = stack[:16384] + "... [truncated]"
        
        error_doc = {
            "ts": datetime.now(timezone.utc),
            "kind": "server",
            "error_type": "StarletteHTTPException",
            "message": str(exc.detail)[:1000],
            "stack": stack,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "anon_id": anon_id,
            "user_id": user_id,
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
            "trace_id": trace_id,
        }
        insert_error_log(error_doc)
    except Exception as e:
        logger.warning(f"Failed to log error in exception handler: {e}")
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    
    # Error log 기록
    try:
        anon_id = get_anon_id(request)
        user_id = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        trace_id = getattr(request.state, "trace_id", None)
        
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if len(stack.encode("utf-8")) > 16384:
            stack = stack[:16384] + "... [truncated]"
        
        error_doc = {
            "ts": datetime.now(timezone.utc),
            "kind": "server",
            "error_type": type(exc).__name__,
            "message": str(exc)[:1000],
            "stack": stack,
            "path": request.url.path,
            "method": request.method,
            "status_code": 500,
            "anon_id": anon_id,
            "user_id": user_id,
            "ip": ip_ua_ref["ip"],
            "user_agent": ip_ua_ref["user_agent"],
            "referer": ip_ua_ref["referer"],
            "trace_id": trace_id,
        }
        insert_error_log(error_doc)
    except Exception as e:
        logger.warning(f"Failed to log error in exception handler: {e}")
    
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    return response

# === Startup Hook ===
@app.on_event("startup")
async def _on_startup():
    # MongoDB 연결 정보 로그 출력
    try:
        from adapters.persistence.mongo import get_db
        db = get_db()
        db_env = os.getenv("MONGO_DB", "arcanaverse")
        mongo_uri = os.getenv("MONGO_URI", "")
        
        # URI 마스킹 (user/password 제거)
        if mongo_uri:
            try:
                # user:password@host 형태를 user:***@host로 마스킹
                if "@" in mongo_uri:
                    parts = mongo_uri.split("@")
                    if "://" in parts[0]:
                        scheme_userpass = parts[0]
                        host_part = "@".join(parts[1:])
                        if ":" in scheme_userpass.split("://")[1]:
                            scheme = scheme_userpass.split("://")[0]
                            userpass = scheme_userpass.split("://")[1]
                            user = userpass.split(":")[0]
                            masked_uri = f"{scheme}://{user}:***@{host_part}"
                        else:
                            masked_uri = mongo_uri
                    else:
                        masked_uri = mongo_uri
                else:
                    masked_uri = mongo_uri
            except Exception:
                masked_uri = "***"
        else:
            masked_uri = "not_set"
        
        logger.info(f"[BOOT] DB_NAME env={db_env}")
        logger.info(f"[BOOT] Mongo db.name={db.name}")
        logger.info(f"[BOOT] Mongo URI (masked)={masked_uri}")
    except Exception as e:
        logger.warning(f"[BOOT] Failed to log MongoDB connection info: {e}")
    
    # 인덱스 초기화
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


# === OpenAI 테스트 엔드포인트 ===
from pydantic import BaseModel

class TestOpenAIChatRequest(BaseModel):
    message: str

@app.post("/api/test-openai-chat")
def test_openai_chat(req: TestOpenAIChatRequest):
    """
    OpenAI API 연동 확인용 테스트 엔드포인트
    
    요청:
        {"message": "안녕"}
    
    응답:
        {"reply": "..."}
    """
    try:
        from adapters.external.openai import generate_chat_completion
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant for Arcanaverse TRPG."},
            {"role": "user", "content": req.message}
        ]
        
        reply = generate_chat_completion(
            messages=messages,
            temperature=0.7,
        )
        
        return {"reply": reply}
    except ValueError as e:
        return {"error": str(e), "reply": ""}
    except Exception as e:
        return {"error": str(e), "reply": ""}
