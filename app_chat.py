import os, time, uuid
from typing import Dict, List, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from embedder import embed

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION  = os.getenv("COLLECTION", "my_docs")
SESSION_COOKIE = "sid"
MAX_TURNS = 12
SESSION_TTL = 60*60*6

SESSIONS: Dict[str, Dict[str, Any]] = {}

SYS_TRPG = """너는 TRPG 마스터다. 플레이어와 협력해 장면을 한 섹션씩 진행한다.
원칙:
- 장면은 5~8문장, 말풍선/행동/설명 균형
- 다음에 할 수 있는 선택지 2~3개 제안
- 플레이어의 톤을 받아주되, 세계관/인물/대사에 일관성 부여
- 한국어로 자연스럽게 말한다
"""

SYS_QA = """너는 유능한 한국어 도우미다. 간결하고 정확하게 답하며, 모르면 모른다고 말한다.
가능하면 검색 컨텍스트를 근거로 자연스럽게 설명하라.
"""

def retrieve_context(query: str, k: int = 5) -> str:
    qvec = embed([query])[0]
    cli = QdrantClient(url=QDRANT_URL)
    res = cli.query_points(collection_name=COLLECTION, query=qvec, limit=k, with_payload=True)
    chunks = []
    for p in getattr(res, "points", []):
        payload = getattr(p, "payload", {}) or {}
        txt = payload.get("text", "")
        if txt:
            chunks.append(txt)
    return "\n\n".join(chunks)

def get_or_create_sid(req: Request) -> str:
    sid = req.cookies.get(SESSION_COOKIE)
    if not sid:
        sid = uuid.uuid4().hex
    sess = SESSIONS.get(sid, {"ts": time.time(), "history": []})
    sess["ts"] = time.time()
    purge_time = time.time() - SESSION_TTL
    for k in list(SESSIONS.keys()):
        if SESSIONS[k]["ts"] < purge_time:
            del SESSIONS[k]
    SESSIONS[sid] = sess
    return sid

def build_messages(mode: str, history: List[dict], user_msg: str, context: str):
    sys_prompt = SYS_TRPG if mode == "trpg" else SYS_QA
    ctx_block = f"\n[검색 컨텍스트]\n{context}\n" if context else ""
    msgs = [{"role": "system", "content": sys_prompt + ctx_block}]
    msgs.extend(history[-MAX_TURNS*2:])
    msgs.append({"role": "user", "content": user_msg})
    return msgs

class ChatIn(BaseModel):
    message: str
    mode: str = "qa"
    model: str = "llama3.1"
    temperature: float = 0.7
    top_p: float = 0.9

app = FastAPI(title="RAG Chat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,   # 세션 쿠키를 쓰므로 True 유지
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: Request, body: ChatIn):
    sid = get_or_create_sid(req)
    sess = SESSIONS[sid]
    llm = ChatOllama(model=body.model, temperature=body.temperature, top_p=body.top_p)

    q = (body.message or "").strip()
    if not q:
        return JSONResponse({"answer": ""}, headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

    ctx = retrieve_context(q)
    messages = build_messages(body.mode, sess["history"], q, ctx)
    ans = llm.invoke(messages)
    text = getattr(ans, "content", str(ans))

    sess["history"].extend([{"role":"user","content":q},{"role":"assistant","content":text}])
    sess["history"] = sess["history"][-MAX_TURNS*2:]

    return JSONResponse({"answer": text, "sid": sid},
                        headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

@app.post("/reset")
def reset(req: Request):
    sid = req.cookies.get(SESSION_COOKIE)
    if sid and sid in SESSIONS:
        SESSIONS[sid]["history"] = []
    return {"ok": True}

# 동일 오리진 제공: chat.html을 서버가 직접 서빙
app.mount("/", StaticFiles(directory=".", html=True), name="static")