import os, json, argparse, sys
from pathlib import Path
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from embedder import embed

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("COLLECTION", "my_docs")
HIST_PATH   = Path(".chat_history.json")

# ----- 간단 파일 기반 메모리 (최근 N턴 유지) -----
def load_history(n_turns:int=8)->List[Dict[str,str]]:
    if HIST_PATH.exists():
        try:
            data = json.loads(HIST_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # 마지막 n_turns*2(사용자/어시스턴트)만 유지
                return data[-(n_turns*2):]
        except Exception:
            pass
    return []

def save_history(history:List[Dict[str,str]]):
    try:
        HIST_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

# ----- RAG 검색 -----
def retrieve_context(query:str, k:int=5)->str:
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

# ----- 프롬프트 -----
# SYS_TRPG = """너는 TRPG 마스터다. 플레이어(사용자)와 협력해 장면을 한 섹션씩 진행한다.
#원칙:
#- 장면은 5~8문장, 말풍선/행동/설명 균형
#- 다음에 할 수 있는 선택지 2~3개 제안
#- 노골적 성적/선정적 표현은 피하고, 15세 이용가 톤 유지
#- 플레이어의 톤을 받아주되, 세계관/인물/대사에 일관성 부여
#- 한국어로 자연스럽게 말한다
#"""
SYS_TRPG = """너는 TRPG 마스터다. 플레이어(사용자)와 협력해 장면을 한 섹션씩 진행한다.
원칙:
- 장면은 5~8문장, 말풍선/행동/설명 균형
- 다음에 할 수 있는 선택지 2~3개 제안
- 플레이어의 톤을 받아주되, 세계관/인물/대사에 일관성 부여
- 한국어로 자연스럽게 말한다
"""

SYS_QA = """너는 유능한 도우미다. 답변은 간결하고 정확하게 한국어로 작성한다.
가능하면 근거(컨텍스트)를 자연스럽게 녹여 설명한다.
모르겠으면 모른다고 말하고, 추측하지 않는다.
"""

def build_messages(mode:str, history:List[Dict[str,str]], query:str, context:str)->List[Dict[str,str]]:
    sys_prompt = SYS_TRPG if mode=="trpg" else SYS_QA
    ctx_block = f"\n[검색 컨텍스트]\n{context}\n" if context else ""
    msgs = [{"role":"system","content": sys_prompt + ctx_block}]
    msgs.extend(history)  # [{"role":"user"...}, {"role":"assistant"...}, ...]
    msgs.append({"role":"user","content": query})
    return msgs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["qa","trpg"], default="qa", help="대화 모드 선택")
    ap.add_argument("--model", default="llama3.1", help="Ollama 모델 이름")
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--top_p", type=float, default=0.9)
    ap.add_argument("question", nargs="*", help="질문 (비우면 REPL)")
    args = ap.parse_args()

    llm = ChatOllama(model=args.model, temperature=args.temp, top_p=args.top_p)
    history = load_history()

    # 단발 질문 모드
    if args.question:
        q = " ".join(args.question)
        context = retrieve_context(q)
        messages = build_messages(args.mode, history, q, context)
        ans = llm.invoke(messages)
        print(ans.content if hasattr(ans,"content") else ans)
        # 히스토리 반영
        history.extend([{"role":"user","content":q},{"role":"assistant","content":ans.content}])
        save_history(history)
        return

    # REPL 모드
    print(f"[{args.mode.upper()} 모드] 종료: /exit, 히스토리 초기화: /clear, 모델: {args.model}")
    while True:
        try:
            q = input("🙂> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not q: 
            continue
        if q == "/exit":
            break
        if q == "/clear":
            history = []
            save_history(history)
            print("(히스토리 초기화)")
            continue

        ctx = retrieve_context(q)
        messages = build_messages(args.mode, history, q, ctx)
        ans = llm.invoke(messages)
        text = ans.content if hasattr(ans,"content") else str(ans)
        print("🤖>", text, "\n")
        # 히스토리 축적
        history.extend([{"role":"user","content":q},{"role":"assistant","content":text}])
        save_history(history)

if __name__ == "__main__":
    main()
