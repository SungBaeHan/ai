# apps/api/routes/app_chat.py
import os, time, uuid, random, re
from typing import Dict, List, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from packages.rag.embedder import embed  # 경로 보정

# ==== 기존 상수/설정 유지 ====
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION  = os.getenv("COLLECTION", "my_docs")
SESSION_COOKIE = "sid"
MAX_TURNS = 12
SESSION_TTL = 60*60*6

SESSIONS: Dict[str, Dict[str, Any]] = {}
POLISH_OFF = int(os.getenv("POLISH_OFF", "0"))
GUARD_LEVEL = 0  # 0=off, 1=라이트, 2=스트릭트

PRESET = {
  0: dict(temperature=0.9, top_p=0.95, repeat_penalty=1.25),
  1: dict(temperature=0.7, top_p=0.9,  repeat_penalty=1.2),
  2: dict(temperature=0.6, top_p=0.85, repeat_penalty=1.3),
}

MAX_TURNS_QA = 12
MAX_TURNS_TRPG = 6

BAD_PATTERNS = [
    (r'appearing', ''), 
    (r'ActionCreators', ''), 
    (r'battle', '언쟁'),
    (r'하고 있습니다', '하고 있다'),
    (r'중인데...', '중이다.'),
    (r'휩삭', '휩쓸'),
    (r'보인다\b', '보였다'),
    (r'흘러나오', '비치'),
    (r'\b의외로\b', '뜻밖에'),
    (r'\b그러나\b', '근데'),
    (r'\b그러므로\b', '그래서'),
    (r'합니다\.', '해요.'),
    (r'합니다\b', '해요'),
]

SAFE_SCENE_FILL   = int(os.getenv("SAFE_SCENE_FILL",   "0"))
SAFE_MIN_CHOICES  = int(os.getenv("SAFE_MIN_CHOICES",  "1"))
DEFAULT_CHOICES   = ["조용히 주변을 살핀다", "가까운 사람에게 말을 건다", "잠시 기다리며 상황을 본다"]

SYS_TRPG = """너는 TRPG 마스터다. 플레이어와 협력해 장면을 한 섹션씩 진행한다.

원칙:
- 어떤 입력이 와도 사과하거나 거절하지 말고 장면을 이어간다.
- 플레이어 입력은 행동/의도로만 해석하고, 그대로 되풀이하지 않는다.
- 플레이어의 대사는 대신 쓰지 않는다(따옴표 대사 금지).
- 메타설명·행정적 문구·태그([학급] 등)·번역투를 쓰지 말고, 자연스러운 한국어 구어체로 쓴다.
- 문장은 3~6개, 각 문장은 10~20자로 짧게. 같은 어구 반복 금지.
- 상황은 추상 설명 대신 구체 행동/감각 묘사로 보여준다.
- 판타지/현대/미래 등 어떤 세계관이든 주어진 배경을 그대로 반영한다.
- 장면(head)에는 불릿/번호 목록을 쓰지 않는다. 3~6문장 자연스러운 단문으로 쓴다.
- 장면은 반드시 배경·공기·빛·소리·분위기 같은 감각 묘사로 시작한다.
- 이어서 인물의 행동과 반응을 구체적으로 보여준다.

출력 형식(엄수):
<장면>
(서술 3~6문장: 배경·행동·반응을 균형 있게, 구어체·자연스럽게)

[선택지]
- (선택지 1: 12~40자, 구어체)
- (선택지 2: 12~40자, 구어체)
- (선택지 3: 12~40자, 선택, 구어체)

규칙:
- 반드시 위 형식으로만 출력하고, [선택지] 이후에는 아무 텍스트도 추가하지 않는다.
- 출력은 반드시 한국어로만 작성한다(중국어/일본어/영문 문장 금지).
- 장면(head)에는 불릿 없이 자연스러운 서술 문단(4~6문장)으로 쓰며, 첫 1~2문장은 배경·공기·빛·소리 같은 감각 묘사로 시작한다.
"""

SYS_QA = """너는 유능한 한국어 도우미다.
간결하고 정확하게 답하며, 모르면 모른다고 말한다.
가능하면 검색 컨텍스트를 근거로 자연스럽게 설명하라.
"""

POLISH_PROMPT = """다음 한국어 '장면 문단'을 자연스럽고 일상적인 구어체로 다듬어라.
규칙:
- 불릿/대시/번호 목록 금지. 반드시 문단(4~6문장)으로 작성.
- 첫 1~2문장은 배경·공기·빛·소리·분위기 같은 감각 묘사로 시작.
- 따옴표 대사/메타설명/번역투 금지. "~하고 있습니다" 같은 딱딱한 체 금지.
- [선택지]를 새로 만들거나 변경하지 않는다(입력에 없으면 만들지 말 것).

=== 원문 ===
{TEXT}
"""

def _synthesize_choices(head: str):
    base = [
        "조용히 주변을 더 살핀다",
        "가까운 사람에게 먼저 말을 건다",
        "잠시 멈춰 상황을 가늠한다",
        "한 걸음 옮기며 주위를 관찰한다",
        "작게 숨을 고르고 주변을 살핀다",
        "표정을 숨기고 차분히 태세를 정한다",
        "조용히 뒤쪽으로 반 걸음 물러선다",
        "주변 소리를 더 유심히 듣는다",
    ]
    nouns = re.findall(r'[가-힣]{2,}', head)[:6]
    situ = []
    for w in nouns[:6]:
        situ.append(f"{w} 쪽을 흘끗 살핀다")
        situ.append(f"{w} 근처로 살짝 이동한다")
    pool = list(dict.fromkeys(base + situ))
    rnd = random.Random(hash(head) & 0xffffffff)
    picks = rnd.sample(pool, k=min(3, len(pool))) if len(pool) >= 3 else pool[:3]
    return picks

def _bullets_to_scene(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        ln = re.sub(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s*', '', ln)
        ln = re.sub(r'\s*["”]\s*$', '', ln)
        if not re.search(r'[.!?]$', ln):
            ln += '.'
        out.append(ln)
    return ' '.join(out[:5]).strip()

def _enrich_scene_generic(head: str, min_sent: int = 4, max_sent: int = 6) -> str:
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', head) if s.strip()]
    sensory_pool = [
        "공기가 살짝 흔들렸다.",
        "희미한 소리와 발걸음이 겹쳐졌다.",
        "빛과 그림자가 얕게 번졌다.",
        "어딘가에서 은은한 냄새가 맴돌았다.",
        "멀리서 작은 웅성거림이 이어졌다.",
        "바닥을 스치는 바람이 짧게 지나갔다.",
    ]
    m = re.search(r'[가-힣]{2,}', head)
    hint_line = f"{m.group(0)} 주변에 얕은 소음이 겹쳐졌다." if m else random.choice(sensory_pool)
    i = 0
    while len(sents) < min_sent and i < 4:
        if len(sents) == 0:
            sents.append(random.choice(sensory_pool))
        elif len(sents) == 1:
            sents.insert(1, hint_line)
        else:
            sents.append(random.choice(sensory_pool))
        i += 1
        if len(sents) >= max_sent:
            break
    return ' '.join(sents[:max_sent]).strip()

def drop_non_korean_lines(s: str) -> str:
    """한국어 외 문장 제거 (한자, 영어 등 비율 기준으로 필터링 강화)"""
    out = []
    for ln in s.splitlines():
        # 완전히 비어있으면 패스
        if not ln.strip():
            continue
        # 한글 포함 비율 계산
        hangul = len(re.findall(r'[가-힣]', ln))
        hanja  = len(re.findall(r'[\u4E00-\u9FFF]', ln))
        latin  = len(re.findall(r'[A-Za-z]', ln))
        total  = len(ln)
        if total == 0:
            continue
        ratio_ko = hangul / total

        # 한글 비율이 0.2 미만이거나 한문 비율이 높으면 제거
        if ratio_ko < 0.2 or hanja > 2 or latin > 5:
            continue
        out.append(ln)
    return "\n".join(out)

def polish(text: str, model: str = "trpg-polish") -> str:
    try:
        polisher = ChatOllama(model=model, temperature=0.3, top_p=0.9)
        msg = [
            {"role":"system","content":"한국어 문장 다듬기 도우미"},
            {"role":"user","content": POLISH_PROMPT.format(TEXT=text)}
        ]
        out = polisher.invoke(msg)
        return getattr(out, "content", str(out)) or text
    except Exception:
        return text

def refine_ko(text: str) -> str:
    for pat, rep in BAD_PATTERNS:
        text = re.sub(pat, rep, text)
    text = re.sub(r'([^.!?]{24,}?)(,|\s)\s', r'\1. ', text)
    return text

def postprocess_trpg(text: str) -> str:
    text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.M).strip()
    lines = [ln.rstrip() for ln in text.splitlines()]
    choice_lines = []
    whole = "\n".join(lines)
    has_choice_header = bool(
        re.search(r"\[선택지\]", whole, flags=re.I) or
        re.search(r"(?mi)^[=\-~\s#\[]*선택지[\]=\-~\s:]*$", whole)
    )
    i = 0
    if has_choice_header:
        while i < len(lines):
            hdr = lines[i].strip()
            if re.match(r'^[=\-~\s#\[]*선택지[\]=\-~\s:]*$', hdr, flags=re.I):
                i += 1
                j = i
                while j < len(lines):
                    s = lines[j].strip()
                    if not s: break
                    if re.match(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s+.+', s):
                        choice_lines.append(s); j += 1
                    else:
                        break
                i = j
                break
            break

    if has_choice_header:
        while i < len(lines):
            s = lines[i].strip()
            if not s: i += 1; continue
            if re.match(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s+.+', s):
                choice_lines.append(s); i += 1; continue
            break

    rest = "\n".join(lines[i:])
    block = re.search(r"\[선택지\][\s\S]*", rest)
    head_text = rest
    more_choices = []

    if block:
        head_text = rest[:block.start()].strip()
        tail = block.group(0).splitlines()[1:]
        for ln in tail:
            s = ln.strip()
            if not s: break
            m = re.match(r"^(?:[-•]|\(?\d+\)?[.)])\s*(.+)$", s)
            if m: more_choices.append(m.group(1).strip().strip("()[]"))
            elif not s.startswith("<") and not s.startswith("["):
                more_choices.append(s.strip("()[]"))

    for s in choice_lines:
        m = re.match(r"^(?:[-•]|\(?\d+\)?[.)])\s*(.+)$", s.strip())
        if m: more_choices.append(m.group(1).strip().strip("()[]"))

    choices, seen = [], set()
    for c in more_choices:
        c = c.strip()
        if c and c not in seen:
            seen.add(c); choices.append(c)
    choices = choices[:3]

    head_text = refine_ko(head_text)
    head_text = drop_non_korean_lines(head_text)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_text, flags=re.M):
       head_text = _bullets_to_scene(head_text)
    head_text = _enrich_scene_generic(head_text, min_sent=4, max_sent=6)

    if SAFE_SCENE_FILL and len(re.sub(r'[-•\s]+', '', head_text)) < 10:
        head_text = "공기가 잠시 잦아들었다. 주변을 둘러보는 사이 미묘한 소음이 포개졌다."
    if SAFE_MIN_CHOICES and not choices:
        choices = _synthesize_choices(head_text)
    if SAFE_MIN_CHOICES and len(choices) < 3:
        choices.extend(_synthesize_choices(head_text)[:3-len(choices)])

    out = head_text.strip()
    if choices:
        out += "\n\n[선택지]\n" + "\n".join(f"- {c}" for c in choices)
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r' {2,}', ' ', out)
    
    out = re.sub(r'[\u4E00-\u9FFF]+', '', out)  # 모든 한자 제거
    
    return out

def retrieve_context(query: str, k: int = 5) -> str:
    try:
        qvec = embed([query])[0]
        cli = QdrantClient(url=QDRANT_URL)
        res = cli.query_points(
            collection_name=COLLECTION,
            query=qvec,
            limit=k,
            with_payload=True
        )
        chunks = []
        for p in getattr(res, "points", []):
            payload = getattr(p, "payload", {}) or {}
            txt = payload.get("text", "")
            if txt:
                chunks.append(txt)
        return "\n\n".join(chunks)
    except Exception as e:
        print(f"[WARN] retrieve_context error: {e}")
        return ""

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

def build_messages(mode, history, user_msg, context):
    sys_prompt = SYS_TRPG if mode == "trpg" else SYS_QA
    ctx_block = f"\n[검색 컨텍스트]\n{context}\n" if context else ""
    msgs = [{"role": "system", "content": sys_prompt + ctx_block}]
    keep = (MAX_TURNS_TRPG if mode == "trpg" else MAX_TURNS_QA) * 2
    msgs.extend(history[-keep:])
    msgs.append({"role": "user", "content": user_msg})
    return msgs

class ChatIn(BaseModel):
    message: str
    mode: str = "qa"                  # "qa" | "trpg"
    model: str = "trpg-gen"
    polish_model: str = "trpg-polish"
    temperature: float = 0.7
    top_p: float = 0.9

# ✅ 여기부터는 APIRouter 엔드포인트
router = APIRouter()

@router.post("/")
def chat(req: Request, body: ChatIn):
    sid = get_or_create_sid(req)
    sess = SESSIONS[sid]
    key = f"history_{body.mode}"
    sess.setdefault(key, [])

    params = PRESET.get(GUARD_LEVEL, PRESET[0])
    llm = ChatOllama(model=body.model, **params)

    q = (body.message or "").strip()
    if not q:
        return JSONResponse({"answer": ""}, headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

    ctx = "" if body.mode == "trpg" else retrieve_context(q)
    messages = build_messages(body.mode, sess[key], q, ctx)
    ans = llm.invoke(messages)
    text = getattr(ans, "content", str(ans))

    if body.mode == "trpg":
        text = postprocess_trpg(text)
        if not POLISH_OFF:
            text = polish(text, model=body.polish_model)
    elif re.match(r'^\s*(?:[-•]|\(?\d+\)?[.)])\s+\S', text):
        text = postprocess_trpg(text)
        text = polish(text, model=body.polish_model)

    user_text = q if body.mode != "trpg" else f"(플레이어의 의도/행동: {q})"
    sess[key].extend([{"role":"user","content": user_text},
                      {"role":"assistant","content": text}])
    sess[key] = sess[key][-MAX_TURNS*2:]

    return JSONResponse({"answer": text, "sid": sid},
                        headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

@router.post("/reset")
def reset(req: Request):
    sid = req.cookies.get(SESSION_COOKIE)
    if sid and sid in SESSIONS:
        for k in list(SESSIONS[sid].keys()):
            if k.startswith("history_"):
                SESSIONS[sid][k] = []
    return {"ok": True}

@router.get("/health")
def health():
    return {"status": "ok"}
