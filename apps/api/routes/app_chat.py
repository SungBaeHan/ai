# ========================================
# apps/api/routes/app_chat.py — 주석 추가 상세 버전
# /v1/chat 엔드포인트: TRPG 모드/QA 모드 대화 처리, 세션 관리, 후처리 등.
# ========================================

import os, time, uuid, random, re              # 표준 라이브러리: 환경/시간/UUID/난수/정규식
from typing import Dict, List, Any             # 타입 힌트

from fastapi import APIRouter, Request         # 라우터, 요청 객체
from fastapi.responses import JSONResponse     # JSON 응답
from pydantic import BaseModel                 # 요청 바디 모델
from qdrant_client import QdrantClient         # Qdrant 클라이언트
from langchain_ollama import ChatOllama        # Ollama 채팅형 LLM
from packages.rag.embedder import embed        # 텍스트 임베딩 함수

# ==== 환경 상수/설정 ====
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")  # Qdrant URL
COLLECTION  = os.getenv("COLLECTION", "my_docs")               # 콜렉션명
SESSION_COOKIE = "sid"                                         # 세션 쿠키 키
MAX_TURNS = 12                                                 # 저장할 대화 턴 수(양방향 *2)
SESSION_TTL = 60*60*6                                          # 세션 보관 시간(초) 6시간

SESSIONS: Dict[str, Dict[str, Any]] = {}                       # 메모리 기반 세션 저장소
POLISH_OFF = int(os.getenv("POLISH_OFF", "0"))                 # 후처리(문장 다듬기) 비활성화 플래그
GUARD_LEVEL = 0  # 0=off, 1=라이트, 2=스트릭트                         # 프리셋 강도

OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_GEN = os.getenv("OLLAMA_MODEL", "trpg-gen")
DEFAULT_POLISH = os.getenv("OLLAMA_POLISH_MODEL", "trpg-polish")

# 모델 파라미터 프리셋: 안정성/창의성 균형을 위해 단계별 설정 제공
PRESET = {
  0: dict(temperature=0.9, top_p=0.95, repeat_penalty=1.25),
  1: dict(temperature=0.7, top_p=0.9,  repeat_penalty=1.2),
  2: dict(temperature=0.6, top_p=0.85, repeat_penalty=1.3),
}

# 모드별 히스토리 유지 최대 턴수
MAX_TURNS_QA = 12
MAX_TURNS_TRPG = 6

# 한국어 자연화/필터링 패턴(간단 교정 규칙)
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

# 안전장치/선택지 보정 관련 플래그 (환경변수로 토글)
SAFE_SCENE_FILL   = int(os.getenv("SAFE_SCENE_FILL",   "0"))
SAFE_MIN_CHOICES  = int(os.getenv("SAFE_MIN_CHOICES",  "1"))
DEFAULT_CHOICES   = ["조용히 주변을 살핀다", "가까운 사람에게 말을 건다", "잠시 기다리며 상황을 본다"]

# TRPG 시스템 프롬프트 — 출력 형식 강제 및 문체/구성 규칙
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

# QA 시스템 프롬프트 — 간결/정확/근거 중심
SYS_QA = """너는 유능한 한국어 도우미다.
간결하고 정확하게 답하며, 모르면 모른다고 말한다.
가능하면 검색 컨텍스트를 근거로 자연스럽게 설명하라.
"""

# 후처리용 폴리싱 프롬프트 — TRPG 장면을 자연스러운 문단으로 다듬음
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
    """장면 내용에서 단어를 뽑아 즉흥적으로 선택지 후보를 생성한다."""
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
    nouns = re.findall(r'[가-힣]{2,}', head)[:6]    # 한글 단어 포착
    situ = []
    for w in nouns[:6]:
        situ.append(f"{w} 쪽을 흘끗 살핀다")
        situ.append(f"{w} 근처로 살짝 이동한다")
    pool = list(dict.fromkeys(base + situ))         # 중복 제거 후 풀 구성
    rnd = random.Random(hash(head) & 0xffffffff)    # 내용 기반 고정 시드
    picks = rnd.sample(pool, k=min(3, len(pool))) if len(pool) >= 3 else pool[:3]
    return picks

def _bullets_to_scene(text: str) -> str:
    """불릿 문장을 간단한 자연 문장으로 합쳐 장면 문단으로 전환한다."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        ln = re.sub(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s*', '', ln)  # 불릿 마커 제거
        ln = re.sub(r'\s*["”]\s*$', '', ln)                           # 끝 따옴표 제거
        if not re.search(r'[.!?]$', ln):                               # 문장부호 보장
            ln += '.'
        out.append(ln)
    return ' '.join(out[:5]).strip()                                   # 최대 5문장으로 합침

def _enrich_scene_generic(head: str, min_sent: int = 4, max_sent: int = 6) -> str:
    """장면 문장을 4~6문장 사이로 다듬고 감각적 문장을 보강한다."""
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
    """한국어 비율이 낮거나 한자/영문 비율이 높은 문장은 제거한다."""
    out = []
    for ln in s.splitlines():
        if not ln.strip():
            continue
        hangul = len(re.findall(r'[가-힣]', ln))
        hanja  = len(re.findall(r'[\u4E00-\u9FFF]', ln))
        latin  = len(re.findall(r'[A-Za-z]', ln))
        total  = len(ln)
        if total == 0:
            continue
        ratio_ko = hangul / total
        if ratio_ko < 0.2 or hanja > 2 or latin > 5:  # 임계치 기반 필터링
            continue
        out.append(ln)
    return "\n".join(out)

def polish(text: str, model: str = None) -> str:
    """폴리싱 모델로 장면 문단을 한국어 구어체로 정돈한다(실패 시 원문 반환)."""
    try:
        use_model = model or DEFAULT_POLISH
        polisher = ChatOllama(
            base_url=OLLAMA_BASE,
            model=use_model,
            temperature=0.3,
            top_p=0.9,
            timeout=120,
        )        
        msg = [
            {"role":"system","content":"한국어 문장 다듬기 도우미"},
            {"role":"user","content": POLISH_PROMPT.format(TEXT=text)}
        ]
        out = polisher.invoke(msg)
        return getattr(out, "content", str(out)) or text
    except Exception:
        return text

def refine_ko(text: str) -> str:
    """간단한 어투/어휘 정규식 치환으로 자연스러움을 높인다."""
    for pat, rep in BAD_PATTERNS:
        text = re.sub(pat, rep, text)
    text = re.sub(r'([^.!?]{24,}?)(,|\s)\s', r'\1. ', text)  # 너무 긴 구를 문장으로 분리
    return text

def postprocess_trpg(text: str) -> str:
    """TRPG 응답을 장면+선택지 형식으로 정돈하고 한국어 중심으로 다듬는다."""
    text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.M).strip()
    lines = [ln.rstrip() for ln in text.splitlines()]
    choice_lines = []
    whole = "\n".join(lines)

    # [선택지] 헤더 유무 판단
    has_choice_header = bool(
        re.search(r"\[선택지\]", whole, flags=re.I) or
        re.search(r"(?mi)^[=\-~\s#\[]*선택지[\]=\-~\s:]*$", whole)
    )

    # [선택지] 블록에서 불릿 항목 추출
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

    # 중복 제거 및 최대 3개 제한
    choices, seen = [], set()
    for c in more_choices:
        c = c.strip()
        if c and c not in seen:
            seen.add(c); choices.append(c)
    choices = choices[:3]

    # 장면 본문 정리
    head_text = refine_ko(head_text)
    head_text = drop_non_korean_lines(head_text)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_text, flags=re.M):
       head_text = _bullets_to_scene(head_text)
    head_text = _enrich_scene_generic(head_text, min_sent=4, max_sent=6)

    # 안전장치: 최소 본문/선택지 보장
    if SAFE_SCENE_FILL and len(re.sub(r'[-•\s]+', '', head_text)) < 10:
        head_text = "공기가 잠시 잦아들었다. 주변을 둘러보는 사이 미묘한 소음이 포개졌다."
    if SAFE_MIN_CHOICES and not choices:
        choices = _synthesize_choices(head_text)
    if SAFE_MIN_CHOICES and len(choices) < 3:
        choices.extend(_synthesize_choices(head_text)[:3-len(choices)])

    # 출력 재구성: 장면 + 선택지
    out = head_text.strip()
    if choices:
        out += "\n\n[선택지]\n" + "\n".join(f"- {c}" for c in choices)
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r' {2,}', ' ', out)
    out = re.sub(r'[\u4E00-\u9FFF]+', '', out)  # 모든 한자 제거
    return out

def retrieve_context(query: str, k: int = 5) -> str:
    """QA 모드에서 사용할 검색 컨텍스트를 Qdrant에서 조회한다."""
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
    """요청 쿠키에서 세션 아이디를 가져오거나 새로 생성한다.
    동시에 만료된 세션을 정리한다."""
    sid = req.cookies.get(SESSION_COOKIE)
    if not sid:
        sid = uuid.uuid4().hex
    sess = SESSIONS.get(sid, {"ts": time.time(), "history": []})
    sess["ts"] = time.time()                                  # 최근 접근 시간 업데이트

    # TTL 초과 세션 정리
    purge_time = time.time() - SESSION_TTL
    for k in list(SESSIONS.keys()):
        if SESSIONS[k]["ts"] < purge_time:
            del SESSIONS[k]

    SESSIONS[sid] = sess
    return sid

def build_messages(mode, history, user_msg, context):
    """Ollama 대화 메시지 배열을 모드에 맞춰 구성한다."""
    sys_prompt = SYS_TRPG if mode == "trpg" else SYS_QA
    ctx_block = f"\n[검색 컨텍스트]\n{context}\n" if context else ""
    msgs = [{"role": "system", "content": sys_prompt + ctx_block}]      # 시스템 메시지
    keep = (MAX_TURNS_TRPG if mode == "trpg" else MAX_TURNS_QA) * 2     # 양방향 길이
    msgs.extend(history[-keep:])                                         # 최근 히스토리만 유지
    msgs.append({"role": "user", "content": user_msg})                   # 현재 사용자 질의
    return msgs

class ChatIn(BaseModel):
    """POST /v1/chat 바디 스키마 — 기본값 포함"""
    message: str
    mode: str = "qa"                  # "qa" | "trpg"
    model: str = "trpg-gen"
    polish_model: str = "trpg-polish"
    temperature: float = 0.7
    top_p: float = 0.9

# 라우터 인스턴스
router = APIRouter()

@router.post("/")
def chat(req: Request, body: ChatIn):
    """대화 엔드포인트 — 세션 관리, RAG 컨텍스트, 후처리까지 수행한 최종 응답을 반환한다."""
    sid = get_or_create_sid(req)                                         # 세션 ID 획득/생성
    sess = SESSIONS[sid]                                                 # 세션 객체
    key = f"history_{body.mode}"                                         # 모드별 히스토리 키
    sess.setdefault(key, [])                                             # 없으면 초기화

    params = PRESET.get(GUARD_LEVEL, PRESET[0])                          # 프리셋 파라미터 선택
    use_model = (body.model or DEFAULT_GEN)
    llm = ChatOllama(                                                    # LLM 인스턴스
        base_url=OLLAMA_BASE,
        model=use_model,
        timeout=120,
        **params
    )

    q = (body.message or "").strip()                                     # 사용자 입력 정리
    if not q:
        # 빈 입력이면 빈 답변과 함께 세션 쿠키 설정만 반환
        return JSONResponse({"answer": ""}, headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

    ctx = "" if body.mode == "trpg" else retrieve_context(q)             # QA 모드에서만 컨텍스트 사용
    messages = build_messages(body.mode, sess[key], q, ctx)              # 메시지 배열 구성
    ans = llm.invoke(messages)                                           # 모델 호출
    text = getattr(ans, "content", str(ans))                             # content 추출(안전처리)

    # TRPG 모드: 형식 정돈 + 폴리싱
    if body.mode == "trpg":
        text = postprocess_trpg(text)
        if not POLISH_OFF:
            text = polish(text, model=(body.polish_model or DEFAULT_POLISH))
    # QA 모드인데 불릿 형태가 나오면 TRPG 후처리를 적용해 읽기 좋게
    elif re.match(r'^\s*(?:[-•]|\(?\d+\)?[.)])\s+\S', text):
        text = postprocess_trpg(text)
        text = polish(text, model=(body.polish_model or DEFAULT_POLISH))

    # 히스토리 업데이트(양방향)
    user_text = q if body.mode != "trpg" else f"(플레이어의 의도/행동: {q})"
    sess[key].extend([{"role":"user","content": user_text},
                      {"role":"assistant","content": text}])
    sess[key] = sess[key][-MAX_TURNS*2:]                                  # 최대 길이 유지

    # 최종 응답 + 세션 쿠키
    return JSONResponse({"answer": text, "sid": sid},
                        headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"})

@router.post("/reset")
def reset(req: Request):
    """현재 세션의 히스토리(모든 모드)를 초기화한다."""
    sid = req.cookies.get(SESSION_COOKIE)
    if sid and sid in SESSIONS:
        for k in list(SESSIONS[sid].keys()):
            if k.startswith("history_"):
                SESSIONS[sid][k] = []
    return {"ok": True}

@router.get("/health")
def health():
    """간단 상태 확인"""
    return {"status": "ok"}
