from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from ask import answer  # ask.py의 answer() 재사용

app = FastAPI(title="RAG API")

# CORS: 파일로 연 html에서도 요청 가능하게 열어둠
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ask")
def ask_get(q: str = Query(..., description="질문")):
    # 간단 방어: 공백만 들어오면 빈 문자열 반환
    q = (q or "").strip()
    if not q:
        return {"answer": ""}
    return {"answer": answer(q)}
