# ========================================
# apps/api/main.py — 주석 추가 상세 버전
# FastAPI 앱의 엔트리포인트. 정적 파일 마운트, HTML 라우트, API 라우터 조립을 담당한다.
# ========================================

import os                                   # 표준 라이브러리: 경로 조합 및 파일 여부 확인에 사용
from fastapi import FastAPI                 # FastAPI 애플리케이션 본체
from fastapi.middleware.cors import CORSMiddleware  # CORS 설정 미들웨어
from fastapi.staticfiles import StaticFiles # 정적 파일 제공
from fastapi.responses import FileResponse, PlainTextResponse  # HTML 파일 또는 안내 텍스트 응답

# 라우터 모듈 임포트 — 각 기능별 엔드포인트가 모여 있는 모듈들
from apps.api.routes import app_chat, app_api, characters

# FastAPI 인스턴스 생성: 문서 제목/버전/설명을 포함
app = FastAPI(
    title="AI TRPG MVP API",                # 문서/Swagger에서 보이는 서비스 이름
    version="2.0.0",                        # 버전 문자열
    description="LangChain + RAG + Redis + Mongo + Qdrant 기반 API",  # 서비스 설명
)

# ------------------------------
# CORS 설정 — 개발 단계에서는 전부 허용(운영에서는 도메인을 제한 권장)
# ------------------------------
app.add_middleware(
    CORSMiddleware,                         # CORS를 처리하는 미들웨어 추가
    allow_origins=["*"],                    # 모든 Origin 허용
    allow_credentials=True,                 # 쿠키 등 자격 증명 포함 허용
    allow_methods=["*"],                    # 모든 HTTP 메소드 허용
    allow_headers=["*"],                    # 모든 헤더 허용
)

# ------------------------------
# 경로 상수 정의 — 파일 시스템 상의 폴더 구조를 계산
# ------------------------------
APPS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 현재 파일(apps/api/main.py) 기준 apps 폴더 경로
ROOT_DIR = os.path.dirname(APPS_DIR)                                     # 프로젝트 루트
WEB_DIR  = os.path.join(APPS_DIR, "web-html")                            # 웹 정적 자원(html/css/js)이 있는 폴더

ASSETS_DIR     = os.path.join(WEB_DIR, "assets")                         # 이미지/폰트 등 정적 리소스 폴더
JSON_DIR_WEB   = os.path.join(WEB_DIR, "json")                           # 웹 폴더 내 /json (있으면 우선 사용)
JSON_DIR_DATA  = os.path.join(ROOT_DIR, "data", "json")                  # 대체 경로: /data/json

def safe_mount(url_path: str, dir_path: str, name: str):
    """지정한 디렉토리가 존재할 때만 StaticFiles를 마운트한다.
    - 존재하지 않으면 경고만 출력하고 런타임 에러를 피한다."""
    if os.path.isdir(dir_path):                                          # 폴더가 실제 존재하는지 확인
        app.mount(url_path, StaticFiles(directory=dir_path), name=name)  # 해당 URL 경로에 정적 폴더 마운트
    else:
        print(f"[WARN] skip mount {url_path} -> {dir_path} (not found)") # 없는 경우 경고 로그

# 정적 폴더 /assets 마운트 시도
safe_mount("/assets", ASSETS_DIR,   "assets")

# /json 경로는 웹 폴더가 우선이며, 없으면 data/json을 사용
if os.path.isdir(JSON_DIR_WEB):                                          # 웹 폴더의 json 폴더가 있으면
    safe_mount("/json", JSON_DIR_WEB, "json-web")                        # /json -> apps/web-html/json
elif os.path.isdir(JSON_DIR_DATA):                                       # 없으면 data/json 폴더 검사
    safe_mount("/json", JSON_DIR_DATA, "json-data")                      # /json -> data/json
else:
    print("[WARN] no JSON directory found for /json")                    # 둘 다 없으면 경고

# ------------------------------
# HTML 라우트 — 홈(/)과 채팅(/chat) 페이지를 파일로 제공
# ------------------------------
def file_or_hint(path: str, hint: str):
    """지정 경로에 파일이 있으면 FileResponse로 반환.
    없으면 친절한 안내 텍스트를 PlainTextResponse로 반환한다."""
    if os.path.isfile(path):                                             # 파일 존재 확인
        return FileResponse(path)                                        # 실제 파일 스트리밍
    return PlainTextResponse(                                            # 없으면 안내 메시지
        f"{hint}\n(찾는 파일이 없습니다: {path})",
        status_code=200,
        media_type="text/plain; charset=utf-8",
    )

@app.get("/")                                                            # GET /
def home_page():
    """홈 페이지 엔드포인트 — home.html을 제공 또는 안내"""
    return file_or_hint(
        os.path.join(WEB_DIR, "home.html"),                              # 파일 경로
        "홈 페이지가 아직 없어요. apps/web-html/home.html 을 추가하세요.",  # 없을 때 안내 문구
    )

@app.get("/chat")                                                        # GET /chat
def chat_page():
    """채팅 페이지 엔드포인트 — chat.html을 제공 또는 안내"""
    return file_or_hint(
        os.path.join(WEB_DIR, "chat.html"),                              # 파일 경로
        "채팅 페이지가 아직 없어요. apps/web-html/chat.html 을 추가하세요.", # 없을 때 안내 문구
    )

# ------------------------------
# API 라우터 조립 — 기능별 라우터를 URL prefix와 함께 등록
# ------------------------------
app.include_router(app_chat.router, prefix="/v1/chat", tags=["Chat"])    # 대화/스토리 엔진
app.include_router(app_api.router,  prefix="/v1/ask",  tags=["Ask"])     # 간단 질의응답
app.include_router(characters.router, prefix="/v1/characters", tags=["Characters"])  # 캐릭터 목록/생성

@app.get("/healthz")                                                     # GET /healthz
def healthz():
    """헬스 체크 — 로드밸런서/모니터링용 간단 상태 확인"""
    return {"status": "ok"}

# ------------------------------
# 로컬 실행 — python apps/api/main.py 로 직접 실행 시 uvicorn 구동
# ------------------------------
if __name__ == "__main__":
    import uvicorn                                                       # 개발 서버
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)  # 코드 변경 자동 반영
