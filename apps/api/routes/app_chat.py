# ========================================
# apps/api/routes/app_chat.py — 캐릭터 메타 확장판
# ========================================

import os, time, uuid, random, re
import asyncio
import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from adapters.external.embedding.sentence_transformer import embed

logger = logging.getLogger(__name__)

QDRANT_URL   = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION   = os.getenv("COLLECTION", "my_docs")
SESSION_COOKIE = "sid"
SESSION_TTL  = 60 * 60 * 6
# 한 캐릭터/모드당 유지할 최근 턴 수
# (유저+AI 1쌍을 1턴으로 봄)
MAX_TURNS      = 3

SESSIONS: Dict[str, Dict[str, Any]] = {}

OLLAMA_BASE     = os.getenv("OLLAMA_HOST", "http://ollama:11434")
DEFAULT_GEN     = os.getenv("OLLAMA_MODEL", "trpg-gen")
DEFAULT_POLISH  = os.getenv("OLLAMA_POLISH_MODEL", "trpg-polish")

# LLM 튜닝 파라미터 (환경변수로도 오버라이드 가능)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))          # 메인 LLM 전체 타임아웃 (초)
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "96"))    # 메인 LLM 토큰 수
POLISH_TIMEOUT = float(os.getenv("POLISH_TIMEOUT", "10"))    # 폴리싱 타임아웃 (초)
POLISH_NUM_PREDICT = int(os.getenv("POLISH_NUM_PREDICT", "64"))

# 폴리싱 사용 여부 (기본 OFF)
ENABLE_POLISH = os.getenv("ENABLE_POLISH", "0") == "1"

SAFE_SCENE_FILL   = int(os.getenv("SAFE_SCENE_FILL",   "0"))
SAFE_MIN_CHOICES  = int(os.getenv("SAFE_MIN_CHOICES", "0"))
DEFAULT_CHOICES   = ["조용히 주변을 살핀다","가까운 사람에게 말을 건다","잠시 기다리며 상황을 본다"]

PRESET = dict(temperature=0.9, top_p=0.95, repeat_penalty=1.25)
MAX_TURNS_QA   = 3
MAX_TURNS_TRPG = 3

BAD_PATTERNS = [(r'하고 있습니다','하고 있다'),(r'합니다\.', '해요.'),(r'합니다\b','해요')]

SYS_TRPG_NOCHOICE = """너는 TRPG 마스터다. 플레이어와 협력해 장면을 한 섹션씩 진행한다.
원칙:
- 어떤 입력이 와도 사과하거나 거절하지 말고 장면을 이어간다.
- 플레이어 입력은 행동/의도로만 해석하고, 그대로 되풀이하지 않는다.
- 플레이어의 대사는 대신 쓰지 않는다(따옴표 대사 금지).
- 메타설명·행정적 문구를 쓰지 말고 자연스러운 한국어 구어체로 쓴다.
- 문장은 3~6개, 각 문장은 10~20자로 짧게. 같은 어구 반복 금지.
- 장면은 반드시 배경·공기·빛·소리 같은 감각 묘사로 시작한다.
출력 형식:
<장면>
(서술 3~6문장: 배경·행동·반응 균형)
규칙:
- [선택지]는 절대 작성하지 않는다.
- 출력은 반드시 한국어.
"""

SYS_TRPG = SYS_TRPG_NOCHOICE + """
출력 형식(엄수):
<장면>
(서술 3~6문장: 배경·행동·반응 균형)
[선택지]
- (선택지 1: 12~40자, 구어체)
- (선택지 2: 12~40자, 구어체)
- (선택지 3: 12~40자, 선택, 구어체)
규칙:
- 반드시 위 형식으로만 출력하고, [선택지] 이후에는 아무 텍스트도 추가하지 않는다.
"""

SYS_QA = """너는 유능한 한국어 도우미다. 간결하고 정확하게 답해라. 모르면 모른다고 말해라."""

POLISH_PROMPT = """다음 한국어 '장면 문단'을 자연스럽고 일상적인 구어체로 다듬어라.
규칙:
- 불릿/번호 목록 금지. 반드시 문단(4~6문장).
- 첫 1~2문장은 배경·공기·빛·소리.
- 따옴표 대사/메타설명/번역투 금지.
- [선택지]를 새로 만들거나 변경하지 않는다.

=== 원문 ===
{TEXT}
"""

def retrieve_context(query: str, k: int = 5) -> str:
    try:
        qvec = embed([query])[0]
        cli = QdrantClient(url=QDRANT_URL)
        res = cli.query_points(collection_name=COLLECTION, query=qvec, limit=k, with_payload=True)
        chunks = []
        for p in getattr(res, "points", []):
            payload = getattr(p, "payload", {}) or {}
            txt = payload.get("text", "")
            if txt: chunks.append(txt)
        return "\n\n".join(chunks)
    except Exception as e:
        print(f"[WARN] retrieve_context error: {e}")
        return ""

def get_or_create_sid(req: Request) -> str:
    sid = req.cookies.get(SESSION_COOKIE) or uuid.uuid4().hex
    sess = SESSIONS.get(sid, {"ts": time.time()})
    sess["ts"] = time.time()
    # TTL purge
    purge = time.time() - SESSION_TTL
    for k in list(SESSIONS.keys()):
        if SESSIONS[k]["ts"] < purge: del SESSIONS[k]
    SESSIONS[sid] = sess
    return sid

def character_to_context(char: Dict[str, Any]) -> str:
    """캐릭터 dict → 시스템 컨텍스트 텍스트(확장)"""
    if not char: return ""
    name = char.get("name") or char.get("id") or "플레이어"
    fields = []

    def add(k, label=None):
        v = char.get(k)
        if v:
            if isinstance(v, (list, tuple)): v = ", ".join(map(str, v))
            fields.append(f"{label or k}: {v}")

    add("archetype", "아키타입")
    add("summary", "요약")
    add("shortBio", "단문 소개")
    add("longBio", "장문 소개")
    add("background", "배경")
    add("greeting", "초기 인사/상황")
    add("scenario", "도입 씬")
    add("tags", "태그")
    # system_prompt는 별도로 rules 블록에 합침
    system_rules = str(char.get("system_prompt") or "").strip()

    profile = f"플레이어 캐릭터 이름: {name}\n" + "\n".join(fields)
    return profile, system_rules

def build_messages(mode: str, history: List[Dict[str,str]], user_msg: str,
                   context: str, char_ctx: str = "", char_rules: str = "", choices: int = 0) -> List[Dict[str,str]]:
    if mode == "trpg":
        sys_prompt = (SYS_TRPG if choices and choices > 0 else SYS_TRPG_NOCHOICE)
    else:
        sys_prompt = SYS_QA

    if mode == "trpg" and char_ctx:
        sys_prompt += f"\n\n[플레이어 캐릭터 프로필]\n{char_ctx}\n"
    if mode == "trpg" and char_rules:
        sys_prompt += f"\n[캐릭터 톤/규칙]\n{char_rules}\n"
    if context:
        sys_prompt += f"\n[검색 컨텍스트]\n{context}\n"

    msgs = [{"role":"system","content": sys_prompt}]
    keep = (MAX_TURNS_TRPG if mode=="trpg" else MAX_TURNS_QA)*2
    msgs.extend(history[-keep:])
    msgs.append({"role":"user","content": user_msg})
    return msgs

def refine_ko(text: str) -> str:
    for pat, rep in BAD_PATTERNS: text = re.sub(pat, rep, text)
    text = re.sub(r'([^.!?]{24,}?)(,|\s)\s', r'\1. ', text)
    return text

def _bullets_to_scene(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        ln = re.sub(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s*', '', ln)
        if not re.search(r'[.!?]$', ln): ln += '.'
        out.append(ln)
    return ' '.join(out[:5]).strip()

def _synthesize_choices(head: str):
    base = ["조용히 주변을 더 살핀다","가까운 사람에게 먼저 말을 건다","잠시 멈춰 상황을 가늠한다"]
    nouns = re.findall(r'[가-힣]{2,}', head)[:6]
    situ = []
    for w in nouns:
        situ.append(f"{w} 쪽을 흘끗 살핀다")
        situ.append(f"{w} 근처로 살짝 이동한다")
    pool = list(dict.fromkeys(base + situ))
    rnd = random.Random(hash(head) & 0xffffffff)
    return rnd.sample(pool, k=min(3, len(pool))) if len(pool) >= 3 else (pool + base)[:3]

def drop_non_korean_lines(s: str) -> str:
    out = []
    for ln in s.splitlines():
        if not ln.strip(): continue
        hangul = len(re.findall(r'[가-힣]', ln))
        hanja  = len(re.findall(r'[\u4E00-\u9FFF]', ln))
        latin  = len(re.findall(r'[A-Za-z]', ln))
        total  = len(ln)
        if total and (hangul/total >= 0.2) and hanja <= 2 and latin <= 5:
            out.append(ln)
    return "\n".join(out)

def _enrich_scene_generic(head: str, min_sent: int = 4, max_sent: int = 6) -> str:
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', head) if s.strip()]
    sensory_pool = ["공기가 살짝 흔들렸다.","희미한 소음이 바닥을 스쳤다.","빛과 그림자가 얕게 번졌다.","은은한 냄새가 맴돈다.","멀리서 작은 웅성거림이 이어졌다."]
    while len(sents) < min_sent and len(sents) < max_sent:
        sents.append(random.choice(sensory_pool))
    return ' '.join(sents[:max_sent]).strip()

def postprocess_trpg(text: str, desired_choices: int = 0) -> str:
    text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.M).strip()
    lines = [ln.rstrip() for ln in text.splitlines()]
    whole = "\n".join(lines)

    # 기존 선택지 추출
    choices: List[str] = []
    if re.search(r"\[선택지\]", whole, flags=re.I):
        tail = whole.split("[선택지]", 1)[1]
        for ln in tail.splitlines():
            s = ln.strip()
            if not s: break
            m = re.match(r"^(?:[-•]|\(?\d+\)?[.)])\s*(.+)$", s)
            if m: choices.append(m.group(1).strip().strip("()[]"))

    head_text = whole.split("[선택지]", 1)[0].strip()
    head_text = refine_ko(head_text)
    head_text = drop_non_korean_lines(head_text)
    if re.search(r'^(?:[-•–—·◦]|[①-⑳]|\(?\d+\)?[.)])\s', head_text, flags=re.M):
        head_text = _bullets_to_scene(head_text)
    head_text = _enrich_scene_generic(head_text, 4, 6)

    desired_choices = max(0, min(3, int(desired_choices or 0)))
    if desired_choices == 0:
        out = re.sub(r'\s*\[선택지\][\s\S]*$', '', head_text).strip()
    else:
        if len(choices) < desired_choices:
            choices.extend(_synthesize_choices(head_text)[:desired_choices-len(choices)])
        uniq, seen = [], set()
        for c in choices:
            if c and c not in seen:
                seen.add(c); uniq.append(c)
        uniq = uniq[:desired_choices]
        out = head_text.strip()
        if uniq:
            out += "\n\n[선택지]\n" + "\n".join(f"- {c}" for c in uniq)

    trans = str.maketrans({"，":", ", "。":". ", "！":"! ", "？":"? ", "；":"; ", "：":": ", "（":"(", "）":")", "【":"[", "】":"]", "「":"\"", "」":"\"", "、":", "})
    out = out.translate(trans)
    out = re.sub(r'[\u3400-\u9FFF]+', '', out)
    out = re.sub(r'\s{2,}', ' ', out)
    out = re.sub(r'\s+([,.!?;:])', r'\1', out)
    out = re.sub(r'([,.!?;:])(?!\s|$)', r'\1 ', out)
    return out.strip()

def polish(text: str, model: Optional[str] = None) -> str:
    try:
        polisher = ChatOllama(
            base_url=OLLAMA_BASE,
            model=(model or DEFAULT_POLISH),
            temperature=0.3,
            top_p=0.9,
            timeout=POLISH_TIMEOUT,
            model_kwargs={
                "keep_alive": "30m",
                "num_predict": POLISH_NUM_PREDICT,
            },
        )
        msg = [
            {"role":"system","content":"너는 한국어 문장 교정 전문가다. 자연스러운 문장으로 다듬어라."},
            {"role":"user","content": POLISH_PROMPT.format(TEXT=text)},
        ]
        out = polisher.invoke(msg)
        cleaned = getattr(out,"content",str(out)) or text
        trans = str.maketrans({"，":", ", "。":". ", "！":"! ", "？":"? ", "；":"; ", "：":": ", "（":"(", "）":")", "【":"[", "】":"]", "「":"\"", "」":"\"", "、":", "})
        cleaned = cleaned.translate(trans)
        cleaned = re.sub(r'[\u3400-\u9FFF]+', '', cleaned)
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)
        cleaned = re.sub(r'([,.!?;:])(?!\s|$)', r'\1 ', cleaned)
        return cleaned.strip()
    except Exception as e:
        print(f"[WARN] polish error: {e}")
        return text

async def _invoke_llm_with_timeout(llm, messages, timeout: float = 20.0):
    """
    ChatOllama.invoke 를 별도 스레드에서 실행하면서,
    전체 호출 시간을 timeout 초로 강제 제한한다.
    """
    try:
        # 블로킹 호출을 스레드풀로 넘기고, asyncio.wait_for 로 전체 시간 제한
        raw = await asyncio.wait_for(
            asyncio.to_thread(llm.invoke, messages),
            timeout=timeout,
        )
        return raw
    except asyncio.TimeoutError:
        logger.exception("❌ LLM overall timeout (>%s sec)", timeout)
        raise HTTPException(
            status_code=500,
            detail=f"LLM 전체 처리 시간이 {timeout}초를 초과했습니다.",
        )
    except Exception as e:
        logger.exception("❌ LLM invoke error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="LLM 처리 중 내부 오류가 발생했습니다.",
        )


class ChatIn(BaseModel):
    message: str
    mode: str = "qa"
    model: str = "trpg-gen"
    polish_model: str = "trpg-polish"
    temperature: float = 0.7
    top_p: float = 0.9
    character_id: Optional[str] = None
    character: Optional[Dict[str, Any]] = None

router = APIRouter()

@router.post("/")
async def chat(req: Request):
    """
    /v1/chat 엔드포인트 (TRPG + QA 겸용)
    - Ollama + (임시로 RAG OFF)
    - Cloudflare 524 방지를 위해:
      * 전체 LLM 호출을 20초로 제한
      * num_predict 를 128로 축소
      * 에러/타임아웃 시 HTTP 500 으로 바로 응답
    """
    try:
        # 1) 요청 파싱
        try:
            data = await req.json()
        except Exception:
            data = {}

        q = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("q")
            or ""
        ).strip()
        mode = (data.get("mode") or "qa").strip().lower()
        use_model = data.get("model") or DEFAULT_GEN
        polish_model = data.get("polish_model") or DEFAULT_POLISH
        temperature = float(data.get("temperature") or 0.7)
        top_p = float(data.get("top_p") or 0.9)
        choices = int(data.get("choices") or 0)

        character = data.get("character") or None
        character_id = data.get("character_id") or (
            (character.get("id") if isinstance(character, dict) else None)
        )

        sid = get_or_create_sid(req)
        sess = SESSIONS[sid]

        # 캐릭터별 히스토리 키
        char_key = "default"
        if isinstance(character, dict):
            char_key = character.get("id") or character.get("name") or "default"
        key = f"history_{mode}_{char_key}"
        sess.setdefault(key, [])

        if not q:
            # 빈 메시지면 그냥 빈 응답
            return JSONResponse(
                {"answer": ""},
                headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"},
            )

        # 2) 컨텍스트 구성
        #    👉 우선 성능 문제 파악을 위해 RAG(검색) OFF: context=""
        context = ""  # 이전: "" if mode == "trpg" else retrieve_context(q)

        char_ctx, char_rules = ("", "")
        if mode == "trpg" and isinstance(character, dict):
            try:
                char_ctx, char_rules = character_to_context(dict(character))
            except Exception:
                char_ctx, char_rules = ("", "")

        # 3) 메인 LLM 설정 (Ollama)
        llm = ChatOllama(
            base_url=OLLAMA_BASE,
            model=use_model,
            timeout=LLM_TIMEOUT,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=PRESET.get("repeat_penalty", 1.25),
            model_kwargs={
                "keep_alive": "30m",
                "num_predict": LLM_NUM_PREDICT,
            },
        )

        messages = build_messages(
            mode=mode,
            history=sess[key],
            user_msg=q,
            context=context,
            char_ctx=char_ctx,
            char_rules=char_rules,
            choices=choices,
        )

        # 4) LLM 호출 (전체 타임아웃 제한)
        raw = await _invoke_llm_with_timeout(llm, messages, timeout=LLM_TIMEOUT)
        text = getattr(raw, "content", str(raw))

        # 5) 후처리 (TRPG 장면 + 선택지 + 폴리싱)
        # 요청에서 polish 플래그를 받을 수 있게 (기본값: None → 상수 ENABLE_POLISH 사용)
        polish_flag = data.get("polish")
        if polish_flag is None:
            use_polish = ENABLE_POLISH  # 환경설정 기본값
        else:
            use_polish = bool(polish_flag)

        if mode == "trpg":
            text = postprocess_trpg(text, desired_choices=choices)
            if use_polish:
                text = polish(text, model=polish_model)
        elif re.match(r"^\s*(?:[-•]|\(?\d+\)?[.)])\s+\S", text):
            # QA 모드인데 목록/불릿 형태면 TRPG 스타일 후처리
            text = postprocess_trpg(text, desired_choices=choices)
            if use_polish:
                text = polish(text, model=polish_model)

        # 6) 히스토리 업데이트
        user_text = q if mode != "trpg" else f"(플레이어의 의도/행동: {q})"
        sess[key].extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": text},
            ]
        )
        sess[key] = sess[key][-MAX_TURNS * 2 :]

        return JSONResponse(
            {"answer": text, "sid": sid},
            headers={"Set-Cookie": f"{SESSION_COOKIE}={sid}; Path=/"},
        )

    except HTTPException:
        # 위에서 올린 HTTPException 은 그대로 전달
        raise
    except Exception as e:
        logger.exception("🔥 /v1/chat/ 라우터 내부 오류 발생! %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Chat Error: {str(e)}",
        )

@router.post("/reset")
def reset(req: Request):
    sid = req.cookies.get(SESSION_COOKIE)
    if sid and sid in SESSIONS:
        for k in list(SESSIONS[sid].keys()):
            if k.startswith("history_"): SESSIONS[sid][k] = []
    return {"ok": True}

@router.get("/health")
def health():
    return {"status": "ok"}
