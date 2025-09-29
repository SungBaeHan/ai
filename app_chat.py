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
from fastapi.responses import RedirectResponse
import random  # ← 추가
import re

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION  = os.getenv("COLLECTION", "my_docs")
SESSION_COOKIE = "sid"
MAX_TURNS = 12
SESSION_TTL = 60*60*6

SESSIONS: Dict[str, Dict[str, Any]] = {}
POLISH_OFF = int(os.getenv("POLISH_OFF", "0"))

GUARD_LEVEL = 0  # 0=off, 1=라이트, 2=스트릭트

# temperature (온도)
# 확률 분포를 얼마나 날카롭게/평평하게 만들지 결정
# 값이 낮을수록 → 확률이 높은 단어 위주로만 선택 (안정적, 반복적)
# 값이 높을수록 → 확률이 낮은 단어도 선택 (창의적, 튀는 답 많음)
# 0.8 = 기본보다 조금 창의적, 하지만 제어 가능

# top_p (누적 확률 컷, nucleus sampling)
# “확률이 높은 상위 토큰 집합”만 남기고 그 안에서만 샘플링
# 예: top_p=0.9 → 누적 확률 90%를 채우는 단어들만 후보로 남김
# 낮출수록 → 안전한 답변 (단조로움)
# 높일수록 → 다양성 ↑
# 👉 0.9 = 상위 90% 범위만 쓴다 → 적당히 다양성 확보

# repeat_penalty (반복 억제 계수)
# 직전 히스토리에 나온 토큰이 다시 등장할 확률을 인위적으로 깎는 계수
# 1.0 = 영향 없음
# 1.1~1.3 = 같은 단어/구문이 반복될수록 페널티 적용 (반복 줄어듦)
# 너무 높이면 → 정상적으로 필요한 단어까지 피해서 어색해짐
# 👉 1.25 = 꽤 강하게 반복 억제 (샤워실 장면 같은 반복 방지에 도움)

PRESET = {
  0: dict(temperature=0.9, top_p=0.95, repeat_penalty=1.25),
  1: dict(temperature=0.7, top_p=0.9,  repeat_penalty=1.2),
  2: dict(temperature=0.6, top_p=0.85, repeat_penalty=1.3),
}

MAX_TURNS_QA = 12
MAX_TURNS_TRPG = 6

# 상단에 이미 존재하는 BAD_PATTERNS만 유지
BAD_PATTERNS = [
    (r'appearing', ''), 
    (r'ActionCreators', ''), 
    (r'battle', '언쟁'),
    (r'하고 있습니다', '하고 있다'),
    (r'중인데...', '중이다.'),
    # 기존 패턴 유지
    (r'휩삭', '휩쓸'),
    (r'보인다\b', '보였다'),
    (r'흘러나오', '비치'),
    (r'\b의외로\b', '뜻밖에'),
    (r'\b그러나\b', '근데'),
    (r'\b그러므로\b', '그래서'),
    (r'합니다\.', '해요.'),
    (r'합니다\b', '해요'),
]

# ----- Soft Fallback Toggles (자유도 vs 안정성) -----
SAFE_SCENE_FILL   = int(os.getenv("SAFE_SCENE_FILL",   "0"))  # 1=짧은 장면 2문장 보정, 0=끄기
SAFE_MIN_CHOICES  = int(os.getenv("SAFE_MIN_CHOICES",  "1"))  # 1=선택지 최소 3개 보장, 0=끄기
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
- 장면(head)에는 불릿/번호 목록을 쓰지 않는다. 3~6문장 자연스러운 단문으로 쓴다.
- 장면(head)은 불릿 없이 자연스러운 서술 문단(4~6문장)으로 쓰며, 첫 1~2문장은 배경·공기·빛·소리 같은 감각 묘사로 시작한다.

"""

# === 추가: QA 시스템 프롬프트 ===
SYS_QA = """너는 유능한 한국어 도우미다.
간결하고 정확하게 답하며, 모르면 모른다고 말한다.
가능하면 검색 컨텍스트를 근거로 자연스럽게 설명하라.
"""

# === 추가: 폴리싱 프롬프트 ===
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
    """
    모델이 [선택지]를 못 뱉었거나 1~2개만 뱉었을 때 보완용.
    - 장면 텍스트에서 단서(명사/동사 느낌)를 가볍게 추출
    - 세계관-중립 기본 후보 + 상황 후보를 합쳐 랜덤 샘플링(3개)
    - 장면별 재현성을 위해 head 해시 기반 시드 사용
    """
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

    # 장면 단서 추출(과한 추론 금지)
    nouns = re.findall(r'[가-힣]{2,}', head)[:6]
    situ = []
    for w in nouns:
        if len(situ) >= 6: break
        # 너무 구체화하지 않고 안전한 틀만 제공
        situ.append(f"{w} 쪽을 흘끗 살핀다")
        situ.append(f"{w} 근처로 살짝 이동한다")

    pool = list(dict.fromkeys(base + situ))  # 중복 제거, 순서 유지

    # 장면별 재현성(같은 장면이면 같은 샘플)
    rnd = random.Random(hash(head) & 0xffffffff)
    picks = rnd.sample(pool, k=min(3, len(pool))) if len(pool) >= 3 else pool[:3]
    return picks

def _bullets_to_scene(text: str) -> str:
    """장면(head) 안의 불릿/번호 줄을 자연스러운 문장으로 변환."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        # 다양한 불릿 토큰 제거(하이픈/점/번호/원문자 등)
        ln = re.sub(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s*', '', ln)
        # 어색한 종결 보정
        ln = re.sub(r'\s*["”]\s*$', '', ln)
        if not re.search(r'[.!?]$', ln):
            ln += '.'
        out.append(ln)
    # 너무 길면 5문장까지만
    return ' '.join(out[:5]).strip()

def _enrich_scene_generic(head: str, min_sent: int = 4, max_sent: int = 6) -> str:
    """
    장면 문장이 부족할 때, 세계관에 구애받지 않는 감각 문장을 보강한다.
    장소 하드코딩 없이, 중립 템플릿 + 텍스트에서 뽑은 단서로만 확장.
    """
    # 1) 문장 나누기
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', head) if s.strip()]

    # 2) 중립 배경 템플릿들
    sensory_pool = [
        "공기가 살짝 흔들렸다.",
        "희미한 소리와 발걸음이 겹쳐졌다.",
        "빛과 그림자가 얕게 번졌다.",
        "어딘가에서 은은한 냄새가 맴돌았다.",
        "멀리서 작은 웅성거림이 이어졌다.",
        "바닥을 스치는 바람이 짧게 지나갔다.",
    ]

    # 3) 현재 텍스트에서 단서 추출(과하게 가정하지 않음)
    #    가장 먼저 보이는 한글 단어 하나를 끌어와 주변 감각으로 확장
    m = re.search(r'[가-힣]{2,}', head)
    if m:
        hint = m.group(0)
        hint_line = f"{hint} 주변에 얕은 소음이 겹쳐졌다."
    else:
        hint_line = random.choice(sensory_pool)

    # 4) 최소 문장수까지 보강
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
    out = []
    for ln in s.splitlines():
        # 한글이 전혀 없고, 한자(중국어)가 다수면 버린다
        if re.search(r'[가-힣]', ln):
            out.append(ln)
        elif re.search(r'[\u4E00-\u9FFF]{4,}', ln):
            continue
        else:
            out.append(ln)
    return "\n".join(out)

def polish_trpg_keep_choices(text: str, model: str = "trpg-polish") -> str:
    """[선택지] 블록은 그대로 두고, 앞쪽 장면(head)만 폴리싱."""
    parts = re.split(r"(\n?\[선택지\][\s\S]*)", text, maxsplit=1)
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    head_polished = polish(head, model=model) if head.strip() else head
    # 🔧 폴리싱 결과가 불릿/대시를 다시 만들었을 때 최종 문단화
    head_polished = drop_non_korean_lines(head_polished)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_polished, flags=re.M):
        head_polished = _bullets_to_scene(head_polished)
    # 문장 수가 짧으면 중립 감각 문장으로 보강(세계관 무관)
    head_polished = _enrich_scene_generic(head_polished, min_sent=4, max_sent=6)
    head_polished = drop_non_korean_lines(head_polished)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_polished, flags=re.M):
       head_polished = _bullets_to_scene(head_polished)
    head_polished = _enrich_scene_generic(head_polished, min_sent=4, max_sent=6)
    return (head_polished.rstrip() + ("\n\n" + tail.lstrip() if tail else "")).strip()

def refine_ko(text: str) -> str:
    for pat, rep in BAD_PATTERNS:
        text = re.sub(pat, rep, text)
    # 문장 길이 과하면 마침표 삽입 (간단 휴리스틱)
    text = re.sub(r'([^.!?]{24,}?)(,|\s)\s', r'\1. ', text)
    return text

def postprocess_trpg(text: str) -> str:
    # 0) 금지 태그 제거
    text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.M).strip()

    lines = [ln.rstrip() for ln in text.splitlines()]
    choice_lines = []

    # 헤더 존재 여부(표준 [선택지] 또는 비표준 '=== 선택지 ===', '선택지:' 등)
    whole = "\n".join(lines)
    has_choice_header = bool(
        re.search(r"\[선택지\]", whole, flags=re.I) or
        re.search(r"(?mi)^[=\-~\s#\[]*선택지[\]=\-~\s:]*$", whole)
    )

    i = 0
    # 0.5) 비표준 '선택지' 헤더가 맨 앞에 오면 그 다음 불릿들을 흡수
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

    # 1) (헤더가 있을 때만) 맨 앞 불릿들을 선택지 후보로 흡수
    if has_choice_header:
        while i < len(lines):
            s = lines[i].strip()
            if not s: i += 1; continue
            if re.match(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s+.+', s):
                choice_lines.append(s); i += 1; continue
            break

    # 2) 남은 본문에서 [선택지] 블록 탐지
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

    # 3) 맨 앞 후보도 정규화
    for s in choice_lines:
        m = re.match(r"^(?:[-•]|\(?\d+\)?[.)])\s*(.+)$", s.strip())
        if m: more_choices.append(m.group(1).strip().strip("()[]"))

    # 4) 선택지 확정(중복 제거, 최대 3)
    choices, seen = [], set()
    for c in more_choices:
        c = c.strip()
        if c and c not in seen:
            seen.add(c); choices.append(c)
    choices = choices[:3]

    # 5) 장면 톤 정리
    head_text = refine_ko(head_text)
    head_text = drop_non_korean_lines(head_text)

    # 5.1) 장면에 불릿이 남아있으면 문장으로 변환(광범위 불릿 대응)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_text, flags=re.M):
       head_text = _bullets_to_scene(head_text)

    # 5.2) 장면이 짧으면 세계관-중립 감각 문장으로 자연스럽게 보강
    head_text = _enrich_scene_generic(head_text, min_sent=4, max_sent=6)

    # 6) 옵션 보정 (SAFE_* 토글)
    if SAFE_SCENE_FILL and len(re.sub(r'[-•\s]+', '', head_text)) < 10:
        head_text = "주변 공기가 잠시 잦아들었다. 린은 교실을 한 바퀴 둘러봤다."
    if SAFE_MIN_CHOICES and not choices:
        choices = _synthesize_choices(head_text)
    if SAFE_MIN_CHOICES and len(choices) < 3:
        choices.extend(_synthesize_choices(head_text)[:3-len(choices)])        

    # 7) 재조립
    out = head_text.strip()
    if choices:
        out += "\n\n[선택지]\n" + "\n".join(f"- {c}" for c in choices)
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r' {2,}', ' ', out)
    return out

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
        # 컬렉션이 없거나 에러 발생 시 컨텍스트 없이 진행
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
    # ⬇️ TRPG에서도 그대로 넣기 (설명체 유도 제거)
    msgs.append({"role": "user", "content": user_msg})
    return msgs

class ChatIn(BaseModel):
    message: str
    mode: str = "qa"                  # "qa" | "trpg"
    model: str = "trpg-gen"           # ← 생성용 기본 모델 프로필
    polish_model: str = "trpg-polish" # ← 폴리시(리라이터)용 기본 모델 프로필
    temperature: float = 0.7
    top_p: float = 0.9

app = FastAPI(title="RAG Chat API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500","http://127.0.0.1:5500",
        "http://localhost:5173","http://127.0.0.1:5173",
        "http://localhost:8080","http://127.0.0.1:8080"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: Request, body: ChatIn):
    sid = get_or_create_sid(req)
    sess = SESSIONS[sid]
    key = f"history_{body.mode}"
    sess.setdefault(key, [])

    # 생성용 LLM: trpg-gen(기본) 사용
    params = PRESET.get(GUARD_LEVEL, PRESET[0])
    llm = ChatOllama(model=body.model, **params)

    q = (body.message or "").strip()
    if not q:
        return JSONResponse({"answer": ""}, headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

    # ctx = retrieve_context(q)
    ctx = "" if body.mode == "trpg" else retrieve_context(q)
    messages = build_messages(body.mode, sess[key], q, ctx)
    ans = llm.invoke(messages)
    text = getattr(ans, "content", str(ans))

    if body.mode == "trpg":
        text = postprocess_trpg(text)
        # text = polish_trpg_keep_choices(text, model=body.polish_model)
        if not POLISH_OFF:
            text = polish_trpg_keep_choices(text, model=body.polish_model)
    elif re.match(r'^\s*(?:[-•]|\(?\d+\)?[.)])\s+\S', text):
        text = postprocess_trpg(text)
        text = polish_trpg_keep_choices(text, model=body.polish_model)

    user_text = q if body.mode != "trpg" else f"(플레이어의 의도/행동: {q})"
    sess[key].extend([{"role":"user","content": user_text},
                      {"role":"assistant","content": text}])
    sess[key] = sess[key][-MAX_TURNS*2:]

    return JSONResponse({"answer": text, "sid": sid},
                        headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

@app.post("/reset")
def reset(req: Request):
    sid = req.cookies.get(SESSION_COOKIE)
    if sid and sid in SESSIONS:
        for k in list(SESSIONS[sid].keys()):
            if k.startswith("history_"):
                SESSIONS[sid][k] = []
    return {"ok": True}


@app.get("/")
def root():
    return RedirectResponse(url="/chat.html")


# 동일 오리진 제공: chat.html을 서버가 직접 서빙
app.mount("/", StaticFiles(directory=".", html=True), name="static")
