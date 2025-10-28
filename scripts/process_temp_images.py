
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# process_temp_images.py
# -----------------------------------------------------------------------------
# 실행 방법 (예시)
#
# 1) 1차 파이프라인: 비전 러프 메타 생성(폴리싱 없음)
#    - 이미지 폴더(temp) 스캔 → 해시/중복검사 → 비전 추론 → DB 저장
#    - 결과는 polish_status='pending' 으로 마킹되어 2차에서 폴리싱 대상이 됨
# 
#    python process_temp_images.py \
#      --mode vision \
#      --temp-dir "/mnt/f/git/ai/apps/web-html/assets/temp" \
#      --img-dir  "/mnt/f/git/ai/apps/web-html/assets/char" \
#      --db       "/mnt/f/git/ai/data/app.sqlite3" \
#      --vision-model "moondream" \
#      --on-duplicate update \
#      --max 10 --parallel 1 --slow-sec 20
#
#    (tip) 배치 종료 후 VRAM 해제:
#      ollama stop moondream
#
# 2) 2차 파이프라인: 폴리싱 전용(텍스트 모델만 사용)
#    - DB에서 polish_status='pending' 레코드들을 가져와 다듬은 후 UPDATE
# 
#    python process_temp_images.py \
#      --mode polish \
#      --db "/mnt/f/git/ai/data/app.sqlite3" \
#      --polish-model "qwen2.5:7b-instruct-q4_K_M" \
#      --batch 50
#
#    (tip) 배치 종료 후 VRAM 해제:
#      ollama stop qwen2.5:7b-instruct-q4_K_M
#
# 공통 팁:
#   - 환경변수 OLLAMA_KEEP_ALIVE=2m 로 콜드스타트 비용을 낮출 수 있음
#   - 이미지 리사이즈 max_side(기본 768) 값을 512로 내리면 비전 속도가 더 빨라짐
#   - sqlite WAL/timeout 튜닝 적용됨. DB가 느림의 원인은 아님(주로 LLM 추론/VRAM)
# =============================================================================

from __future__ import annotations  # 타입 전방 참조 허용
import argparse                    # CLI 인자 파싱
import base64                      # 이미지 b64 인코딩
import hashlib                     # SHA-256 해시
import json                        # JSON 직렬화/역직렬화
import os                          # OS/환경변수 접근
import re                          # 정규표현식
import shutil                      # 파일 이동
import sqlite3                     # SQLite DB
import subprocess                  # 외부 명령(ollama stop 등)
import time                        # 타이밍/epoch
from pathlib import Path           # 경로 유틸
from typing import Any, Dict, List, Tuple, Iterable  # 타입 힌트
import concurrent.futures as cf    # 병렬 스레드
import requests                    # Ollama HTTP 호출

# Pillow(이미지 리사이즈) 시도 – 없으면 원본 그대로 사용
try:
    from PIL import Image          # 이미지 열기/리사이즈
except Exception:
    Image = None                   # 미설치 시 None 처리

# ============================== 환경 파라미터 ================================
LLM_TIMEOUT_SEC = int(os.getenv("META_TIMEOUT_SEC", "35"))   # 텍스트 LLM 타임아웃
LLM_RETRIES     = int(os.getenv("META_RETRIES", "2"))        # 재시도 횟수
LLM_BACKOFF     = float(os.getenv("META_BACKOFF", "1.7"))    # 백오프 계수
LLM_MAX_NEW     = int(os.getenv("META_MAX_NEW", "200"))      # 생성 토큰 상한
DEFAULT_PARALLEL= int(os.getenv("META_PARALLEL", "1"))       # 기본 병렬 수
KEEP_ALIVE      = os.getenv("OLLAMA_KEEP_ALIVE", "2m")       # Ollama keep_alive

# ============================== 태그/힌트 세트 ===============================
GENRE_HINTS = {                                                 # 태그→(세계관, 장르) 힌트
    "군사": ("근미래 지구", "밀리터리"),
    "밀리터리": ("근미래 지구", "밀리터리"),
    "현대": ("현대 지구", "현대물"),
    "사이버": ("디스토피아 지구", "사이버펑크"),
    "중세": ("아르카디아", "하이 판타지"),
    "동양풍": ("천산국", "무협/동양풍 판타지"),
    "서양풍": ("알비온", "클래식 판타지"),
    "도시": ("대도시권", "어반 판타지"),
}
DEFAULT_STYLE = "현장 보고체, 간결하고 긴박한 톤"               # 기본 스타일 톤
TAG_POOL = [                                                    # 기본 태그 풀
    "모험","용병","마법","치유","궁수","검술","도시","시골","귀족","길드",
    "냉정","쾌활","차분","낙천","냉소","진중","열정","신비","소심","대담",
    "동양풍","서양풍","미래","스팀펑크","사이버","중세","현대","바닷가","사막","설원",
]

# ============================== 이름 후보 ================================
KOREAN_FEM_NAMES = [                                            # 이름 후보 리스트
    "세라","하나","리나","유나","미나","레나","유리","아야","미코","사야",
    "레이","리사","에리","미유","소라","하루","유키","미소","지유","은서",
    "아린","나오","리오","히나","유미","라라","하미","유메","미오","리노",
]

# ============================== DB 스키마/마이그레이션 =========================
MIGRATION_COLUMNS = [                                           # 누락 시 추가할 컬럼
    ("archetype", "TEXT"),
    ("background", "TEXT"),
    ("scenario", "TEXT"),
    ("system_prompt", "TEXT"),
    ("greeting", "TEXT"),
    ("detail", "TEXT"),
    ("tags", "TEXT"),
    ("created_at", "INTEGER"),
    ("updated_at", "INTEGER"),
    ("img_hash", "TEXT"),
    ("src_file", "TEXT"),
    ("world","TEXT"),
    ("genre","TEXT"),
    ("style","TEXT"),
    ("vision_model","TEXT"),
    ("polish_model","TEXT"),
    ("polish_status","TEXT"),
    ("meta_version","INTEGER"),
]

def tune_sqlite(conn: sqlite3.Connection, busy_timeout_ms: int = 5000) -> None:
    """SQLite 성능 옵션 적용 및 busy_timeout 설정"""
    cur = conn.cursor()                                        # 커서 획득
    cur.execute("PRAGMA journal_mode=WAL;")                    # WAL 모드
    cur.execute("PRAGMA synchronous=NORMAL;")                  # 동기화 완화
    cur.execute("PRAGMA temp_store=MEMORY;")                   # 임시 메모리 사용
    cur.execute("PRAGMA cache_size=-20000;")                   # 약 20MB 캐시
    cur.execute(f"PRAGMA busy_timeout={busy_timeout_ms};")     # busy 타임아웃
    cur.close()                                                # 커서 종료

def ensure_characters_table(conn: sqlite3.Connection) -> None:
    """characters 테이블 생성 및 마이그레이션(부족 컬럼 추가)"""
    cur = conn.cursor()                                        # 커서 획득
    # 테이블 없으면 생성
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            summary TEXT,
            detail TEXT,
            tags TEXT,
            image TEXT,
            img_hash TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            archetype TEXT,
            background TEXT,
            scenario TEXT,
            system_prompt TEXT,
            greeting TEXT,
            src_file TEXT,
            world TEXT,
            genre TEXT,
            style TEXT,
            vision_model TEXT,
            polish_model TEXT,
            polish_status TEXT,
            meta_version INTEGER
        )
        """
    )
    # 기존 컬럼 목록 확인
    cur.execute("PRAGMA table_info(characters)")
    existing = {row[1] for row in cur.fetchall()}
    # 누락 컬럼 추가
    for col, typ in MIGRATION_COLUMNS:
        if col not in existing:
            cur.execute(f"ALTER TABLE characters ADD COLUMN {col} {typ}")
    # 해시 유니크 인덱스(중복 방지)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_characters_img_hash ON characters(img_hash)")
    conn.commit()                                              # 커밋
    cur.close()                                                # 커서 종료

def image_hash_exists(conn: sqlite3.Connection, h: str) -> bool:
    """이미지 해시 중복 여부 확인"""
    return conn.execute("SELECT 1 FROM characters WHERE img_hash=? LIMIT 1", (h,)).fetchone() is not None

def insert_character_row(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    """캐릭터 신규 INSERT"""
    conn.execute(
        """
        INSERT INTO characters
        (name, summary, detail, tags, image, img_hash, created_at, updated_at,
         archetype, background, scenario, system_prompt, greeting, src_file,
         world, genre, style, vision_model, polish_model, polish_status, meta_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["name"], row["summary"], row["detail"], json.dumps(row["tags"], ensure_ascii=False),
            row["image"], row["img_hash"], int(time.time()), int(time.time()),
            row.get("archetype"), row.get("background"), row.get("scenario"),
            row.get("system_prompt"), row.get("greeting"), row.get("src_file"),
            row.get("world"), row.get("genre"), row.get("style"),
            row.get("vision_model"), row.get("polish_model"), row.get("polish_status"), row.get("meta_version"),
        ),
    )

# ============================== 파일/이미지 유틸 ===============================
def sha256_file(p: Path) -> str:
    """파일 SHA-256 해시 계산"""
    h = hashlib.sha256()                                       # 해시 객체
    with p.open("rb") as f:                                    # 파일 열기
        for chunk in iter(lambda: f.read(1024 * 1024), b""):   # 1MB씩 읽기
            h.update(chunk)                                    # 해시에 누적
    return h.hexdigest()                                       # 16진수 문자열

def safe_ext(p: Path) -> str:
    """허용 확장자 아니면 .jpg로 통일"""
    ext = p.suffix.lower()                                     # 소문자 확장자
    return ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"

def move_to_img_by_hash(src: Path, img_dir: Path, h: str) -> Path:
    """이미지를 해시 기반 파일명으로 목적지 폴더로 이동"""
    dst = img_dir / f"{h[:12]}{safe_ext(src)}"                 # 12자리 해시 + 확장자
    shutil.move(str(src), str(dst))                            # 파일 이동
    return dst                                                 # 목적지 경로 반환

def load_image_as_b64_resized(image_path: str, max_side: int = 768) -> str:
    """긴 변을 max_side로 리사이즈 후 b64 인코딩(Pillow 없으면 원본)"""
    if Image is None:                                          # Pillow 미설치
        with open(image_path, "rb") as f:                      # 파일 원본 열기
            return base64.b64encode(f.read()).decode("utf-8")  # 그대로 b64
    img = Image.open(image_path).convert("RGB")                # 이미지 열고 RGB 변환
    w, h = img.size                                            # 가로/세로
    scale = max(w, h) / float(max_side)                        # 축소 배율
    if scale > 1.0:                                            # 축소가 필요하면
        img = img.resize((int(w/scale), int(h/scale)), Image.LANCZOS)  # 리사이즈
    from io import BytesIO                                     # 메모리 버퍼
    buf = BytesIO()                                            # 버퍼 생성
    img.save(buf, format="JPEG", quality=88)                   # JPEG 저장
    return base64.b64encode(buf.getvalue()).decode("utf-8")    # b64 인코딩

# ============================== 이름/태그 보정 ================================
def coerce_korean_name(raw: str, img_hash: str) -> str:
    """CJK 포함 시 특수문자 제거·8자 제한, 아니면 해시 기반 의사난수 이름"""
    n = (raw or "").strip()                                    # 공백 제거
    if re.search(r"[\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9fff]", n):  # CJK 포함 여부
        n = re.sub(r"[\s\"'`<>|\:/*?\\]+", "", n)              # 특수문자 제거
        return (n[:8] or "세라")                               # 8자 제한
    idx = int((img_hash or "0")[:4], 16) % len(KOREAN_FEM_NAMES)  # 해시→인덱스
    return KOREAN_FEM_NAMES[idx]                               # 후보 중 선택

def enrich_world_fields(name, summary, detail, tags, world, genre, style):
    """world/genre/style 비어있으면 태그/문장으로 추론해 채움"""
    w, g, s = (world or "").strip(), (genre or "").strip(), (style or "").strip()
    # 태그 기반 추론
    if (not w or not g) and isinstance(tags, list):
        for t in tags:
            t = str(t)
            if t in GENRE_HINTS:
                w = w or GENRE_HINTS[t][0]
                g = g or GENRE_HINTS[t][1]
                break
    # 키워드 기반 추론(간단)
    text = f"{summary} {detail}"
    if not g and any(k in text for k in ["총","헬기","작전","부대","군인"]):
        w = w or "근미래 지구"
        g = "밀리터리"
    # 스타일 기본값
    if not s:
        if any(k in text for k in ["무전","상황","보고","대기"]):
            s = "현장 보고체, 간결하고 긴박한 톤"
        else:
            s = DEFAULT_STYLE
    return w or "", g or "", s or DEFAULT_STYLE

# ============================== 표준 스키마(12필드) ============================
def normalize_meta(meta: Any) -> Tuple[str,str,str,List[str],str,str,str,str,str,str,str,str]:
    """입력 경로와 상관없이 12필드 튜플로 맞춤"""
    default = ("세라","밝고 당찬 모험가.","과거를 감춘 채 방랑하는 전사.",[], "모험가","","","","","","","")
    if not isinstance(meta, (list, tuple)):
        return default
    m = list(meta)
    if len(m) < 12:
        m += ["","",""]
    m = m[:12]
    if not isinstance(m[3], list):
        m[3] = []
    return tuple(m)  # type: ignore

# ============================== 로컬 시드 폴백 ================================
def _seed_only_meta(image_name: str, seed: str):
    """LLM 호출 없이 12필드 로컬 생성(최후 폴백)"""
    rnd = int(seed or "0", 16)                                 # 시드 숫자화
    import random as _random                                   # 지역 random
    r = _random.Random(rnd)                                    # 시드 random
    base_name = os.path.splitext(os.path.basename(image_name or ""))[0][:8] or "세라"
    name = base_name if re.search(r"[\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9fff]", base_name) \
        else KOREAN_FEM_NAMES[r.randrange(len(KOREAN_FEM_NAMES))]
    summary = r.choice(["침착하지만 굳센 의지를 지닌 모험가.","잔상 같은 미소를 남기는 해결사."])
    detail  = r.choice(["감정의 파고를 드러내지 않지만, 곁을 지키는 데 서툴지 않다.","약속을 어기지 않는 편이며, 조용히 결과로 말한다."])
    tags    = r.sample(TAG_POOL, 6)
    archetype = r.choice(["모험가","검사","연성술사","추적자"])
    background= r.choice(["변방의 길드에서 시작해 도시로 넘어왔다.","폐항의 창고 거점을 전전했다."])
    scenario  = r.choice(["젖은 자갈길 위, 그녀가 먼저 시선을 들며 묻는다.","안개가 걷히자, 작은 등대 불빛이 숨을 고른다."])
    system_prompt = "구어체, 설정 일관, 장황한 독백 금지. 질문엔 간결히."
    greeting = r.choice(["왔어? 천천히 얘기하자.","괜찮아, 하나씩 확인해 보자."])
    world, genre, style = "", "", ""
    return (name, summary, detail, tags, archetype, background, scenario, system_prompt, greeting, world, genre, style)

# ============================== 텍스트 LLM(폴백) ==============================
def _llm_once(query: str, model_name: str, image_name: str, seed: str):
    """텍스트 LLM 한 번 호출 – 실패 시 호출부에서 로컬 폴백"""
    try:
        from langchain_ollama import ChatOllama                # 최신 래퍼
    except Exception:
        from langchain_community.chat_models import ChatOllama # 구버전 대체

    llm = ChatOllama(                                          # 텍스트 LLM 객체
        model=model_name, temperature=0.8,
        model_kwargs={"num_predict": LLM_MAX_NEW, "repeat_penalty": 1.1},
    )
    # 프롬프트(스키마 명시 + world/genre/style 필수화)
    style_hint = "서늘하고 간결한 문장"
    sys = f"""
너는 TRPG 캐릭터 메타데이터를 한국어로 생성하는 작가다. 모든 출력은 JSON 하나로만 한다.
- 서로 다른 이미지에 대해 같은 문장을 반복하지 말 것.
- 문체: {style_hint}
- 반드시 아래의 모든 키를 포함하고, world/genre/style도 채워 넣을 것.
스키마:
{{
  "name": "이름(2~8자)",
  "archetype": "역할/원형",
  "summary": "한 문장 요약(40~80자)",
  "detail": "인물 설명(150~230자)",
  "background": "세계/인물 배경(200~320자)",
  "scenario": "도입 씬(2~3문장)",
  "system_prompt": "톤/규칙(1~2문단)",
  "greeting": "첫 인사",
  "tags": ["태그1","태그2","태그3","태그4","태그5","태그6"],
  "world": "", "genre": "", "style": ""
}}
""".strip()
    user = f"검색 컨텍스트: {query}\n이미지 파일명: {image_name}\n난수 시드: {seed}\nJSON만 출력".strip()

    out = llm.invoke([{"role":"system","content":sys},{"role":"user","content":user}])
    text = out.content if hasattr(out, "content") else str(out)

    try:
        data = json.loads(text) if text else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    # 실패 시 호출부에서 로컬 폴백 처리
    if not data:
        return (
            "세라", "밝고 당찬 모험가.", "과거를 감춘 채 방랑하는 전사.",
            TAG_POOL[:6], "모험가", "", "", "", "", "", "", ""
        )

    # JSON에서 필요한 값 추출(없으면 기본)
    def S(k, d=""): v=data.get(k,d); return str(v or "").strip()
    def L(k, d): v=data.get(k,d); return v if isinstance(v,list) else d
    return (
        S("name","세라"),
        S("summary","밝고 당찬 모험가."),
        S("detail","과거를 감춘 채 방랑하는 전사."),
        L("tags", TAG_POOL[:6]),
        S("archetype","모험가"),
        S("background",""),
        S("scenario",""),
        S("system_prompt",""),
        S("greeting",""),
    )

def call_llm_with_timeout(query: str, model_name: str, image_name: str, seed: str):
    """텍스트 LLM 호출(타임아웃/재시도) → 실패 시 로컬 폴백 12필드"""
    attempt, delay = 0, 0.25                                   # 재시도/백오프
    while True:
        attempt += 1
        try:
            with cf.ThreadPoolExecutor(max_workers=1) as ex:   # 단일 작업 스레드
                fut = ex.submit(_llm_once, query, model_name, image_name, seed)
                nine = fut.result(timeout=LLM_TIMEOUT_SEC)     # 타임아웃 대기
                return normalize_meta(nine)                    # 12필드 정규화
        except Exception as e:
            msg = str(e)
            # 모델 없음/치명적 → 즉시 로컬 폴백
            if "status code: 404" in msg or "not found" in msg:
                return normalize_meta(_seed_only_meta(image_name, seed))
            # 재시도 초과 → 로컬 폴백
            if attempt > LLM_RETRIES + 1:
                return normalize_meta(_seed_only_meta(image_name, seed))
            time.sleep(delay); delay *= LLM_BACKOFF            # 백오프

# ============================== 비전 LLM 호출 ================================
def _extract_json_block(text: str) -> dict:
    """응답에서 첫 JSON 블록만 파싱"""
    try:
        if isinstance(text, dict): return text                 # 이미 dict면 그대로
        if not text: return {}                                 # 빈 응답
        return json.loads(text)                                # 전체를 JSON 시도
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text or "")              # 중괄호 블록 추출
        if not m: return {}                                    # 없으면 빈 dict
        try: return json.loads(m.group(0))                     # 블록만 파싱
        except Exception: return {}                            # 실패 시 빈 dict

def vision_meta_via_ollama(image_path: str, model_name: str, query: str, seed: str, fallback_model: str):
    """Ollama 비전 모델로 러프 메타 생성, 실패 시 텍스트 폴백"""
    b64 = load_image_as_b64_resized(image_path, max_side=768)  # 이미지 b64(리사이즈)
    payload = {                                                # Ollama chat payload
        "model": model_name,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "messages": [
            {"role":"system","content":
             "한국어만 사용. 아래 스키마의 JSON만 출력. 모든 키 포함(특히 world, genre, style). 반복 금지."},
            {"role":"user","content": f"""
                검색 컨텍스트: {query}
                난수 시드: {seed}
                아래 스키마로 작성(모든 키 포함):
                {{
                  "name":"이름(2~8자)", "archetype":"역할/원형",
                  "summary":"한 문장 요약(40~80자)", "detail":"인물 설명(150~230자)",
                  "background":"세계/인물 배경(200~320자)", "scenario":"도입 씬(2~3문장)",
                  "system_prompt":"톤/규칙(1~2문단)", "greeting":"첫 인사",
                  "tags":["태그1","태그2","태그3","태그4","태그5","태그6"],
                  "world":"", "genre":"", "style":""
                }}""", "images":[b64]}
        ],
        "options": {
            "temperature": 0.4,
            "num_predict": LLM_MAX_NEW,
            "repeat_penalty": 1.15
        }
    }
    try:
        r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=60)  # HTTP 요청
        r.raise_for_status()                                     # HTTP 오류 처리
        data_blob = r.json()                                     # JSON 응답 파싱
        content = (data_blob.get("message", {}) or {}).get("content", "")  # 콘텐츠 추출
        obj = _extract_json_block(content)                       # JSON 블록 파싱
        if not obj or not any(obj.get(k) for k in ("name","summary","detail")):
            raise ValueError("vision returned empty JSON")       # 비어있으면 예외
    except Exception:
        # 비전 실패 시 텍스트 폴백으로 러프 생성
        return call_llm_with_timeout(query, fallback_model, os.path.basename(image_path), seed)

    # JSON → 12필드 구성
    def S(k,d=""): return str(obj.get(k,d) or "").strip()
    def L(k,d): v=obj.get(k,d); return v if isinstance(v,list) else d
    tags = L("tags", []) or TAG_POOL[:6]
    return (
        S("name","세라"), S("summary","밝고 당찬 모험가."), S("detail","과거를 감춘 채 방랑하는 전사."),
        tags, S("archetype","모험가"), S("background",""), S("scenario",""),
        S("system_prompt",""), S("greeting",""), S("world",""), S("genre",""), S("style","")
    )

# ============================== 폴리싱 단계 ================================
def polish_meta(meta12, model_name: str):
    """1차 러프 메타를 텍스트 모델로 다듬어 반환(12필드 유지)"""
    # 입력 12필드 정규화
    (name, summary, detail, tags, archetype,
     background, scenario, system_prompt, greeting,
     world, genre, style) = normalize_meta(meta12)
    # LLM 래퍼 준비
    try:
        from langchain_ollama import ChatOllama
    except Exception:
        from langchain_community.chat_models import ChatOllama
    llm = ChatOllama(
        model=model_name, temperature=0.6,
        model_kwargs={"num_predict": int(os.getenv("META_MAX_NEW","120")), "repeat_penalty": 1.1},
    )
    # 시스템/유저 프롬프트 구성(JSON만 출력)
    sys = """너는 TRPG 캐릭터 메타를 다듬는 편집자다.
- 한국어만 사용.
- 과장/군더더기 없이 간결·일관된 톤.
- world/genre/style에 맞는 어휘 사용.
- JSON만 출력."""
    user = json.dumps({
        "name": name, "archetype": archetype,
        "world": world, "genre": genre, "style": style,
        "tags": tags,
        "draft": {
            "summary": summary, "detail": detail,
            "background": background, "scenario": scenario,
            "system_prompt": system_prompt, "greeting": greeting
        },
        "rules": {
            "summary_len": "40-80자",
            "detail_len": "150-230자",
            "scenario_len": "2-3문장, 120-220자",
            "no_repetition": True
        }
    }, ensure_ascii=False)
    # 호출
    out = llm.invoke([{"role":"system","content":sys},{"role":"user","content":user}])
    # 파싱 실패하면 원본 반환
    try:
        obj = json.loads(getattr(out, "content", str(out)))
    except Exception:
        return (name, summary, detail, tags, archetype, background, scenario, system_prompt, greeting, world, genre, style)
    # 결과 값 결합(없으면 초안 유지)
    def S(k,d=""): return str(obj.get(k,d) or "").strip()
    d = obj.get("draft", {}) if isinstance(obj, dict) else {}
    def D(k,dv=""): return str(d.get(k,dv) or "").strip()
    summary2    = S("summary")    or D("summary")    or summary
    detail2     = S("detail")     or D("detail")     or detail
    background2 = S("background") or D("background") or background
    scenario2   = S("scenario")   or D("scenario")   or scenario
    sys2        = S("system_prompt") or D("system_prompt") or system_prompt
    greet2      = S("greeting")   or D("greeting")   or greeting
    world2      = S("world")      or world
    genre2      = S("genre")      or genre
    style2      = S("style")      or style
    # 12필드로 반환
    return (name, summary2, detail2, tags, archetype, background2, scenario2, sys2, greet2, world2, genre2, style2)

# ============================== Ollama 언로드 유틸 ============================
def ollama_stop(*models: str):
    """배치 종료 시 모델 언로드(VRAM 해제), 실패해도 무시"""
    for m in models:
        if not m: 
            continue
        try:
            subprocess.run(["ollama", "stop", m], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# ============================== 모드별 실행 ================================
def run_mode_vision(args):
    """1차 파이프라인: 이미지→비전 러프 메타→DB 저장(pending)"""
    temp_dir = Path(args.temp_dir); temp_dir.mkdir(parents=True, exist_ok=True)
    img_dir  = Path(args.img_dir);  img_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)                             # DB 연결
    tune_sqlite(conn, args.busy_timeout)                        # SQLite 튜닝
    ensure_characters_table(conn)                               # 테이블/컬럼 보장

    files = [p for p in temp_dir.iterdir() if p.is_file()]      # 파일 나열
    if not files:                                               # 없으면 종료
        print("[PROC] 처리할 파일이 없습니다."); conn.close(); return
    files.sort(key=lambda p: p.stat().st_mtime)                 # 수정시간 기준 정렬
    if args.max and args.max > 0:                               # 최대 개수 제한
        files = files[:args.max]

    print(f"[PROC] 대상 {len(files)}개 파일")                   # 대상 출력

    moved = dup = fail = deleted = 0                            # 카운터 초기화
    t0 = time.perf_counter()                                    # 시작 시각

    def build_todo() -> List[Tuple[Path, str]]:
        """중복 제외 대상 목록 구성"""
        nonlocal dup, fail, deleted
        todo: List[Tuple[Path, str]] = []                       # 결과 리스트
        for fp in files:                                        # 파일마다
            try:
                h = sha256_file(fp)                             # 해시 계산
                if image_hash_exists(conn, h):                  # 중복이면
                    dup += 1                                    # 카운트 증가
                    if args.on_duplicate == "delete":           # 삭제 정책이면
                        try:
                            fp.unlink(missing_ok=True)          # 파일 삭제
                            deleted += 1                        # 삭제 카운트
                            print(f" - 중복 삭제: {fp.name}")   # 로그
                        except Exception as ex:
                            print(f" ! 중복 삭제 실패 {fp.name}: {ex}")
                    else:                                       # skip/update
                        print(f" - 중복 스킵: {fp.name}")       # 로그
                    continue                                    # 다음 파일
                todo.append((fp, h))                            # 처리 목록 추가
            except Exception as e:
                fail += 1                                       # 실패 카운트
                print(f" ! 해시 실패 {fp.name}: {e}")           # 로그
        return todo                                             # 목록 반환

    try:
        todo = build_todo()                                     # 처리 목록 생성
        if not todo:                                            # 없으면 종료
            print(f"[TIMING] {time.perf_counter()-t0:.2f}s")
            print(f"[PROC] 이동 {moved}/중복 {dup}(삭제 {deleted})/실패 {fail}")
            return

        def llm_worker(task):
            """비전 또는 텍스트 폴백으로 러프 메타 생성"""
            fp, h = task                                        # 파일/해시
            t_start = time.perf_counter()                       # 시작 시각
            seed = h[:8]                                        # 시드(해시 앞 8)
            try:
                if args.vision_model:                           # 비전 모델 지정됨
                    meta12 = vision_meta_via_ollama(str(fp), args.vision_model, args.query, seed, args.model)
                else:                                           # 비전 미지정 → 텍스트
                    meta12 = call_llm_with_timeout(args.query, args.model, fp.name, seed)
                t_end = time.perf_counter()                     # 끝 시각
                dur = (t_end - t_start)                         # 소요 시간
                rel_start = (t_start - t0) * 1000               # 전체 시작 대비 ms
                rel_end = (t_end - t0) * 1000                   # 전체 시작 대비 ms
                print(f"   [TIME] {fp.name} start={rel_start:.0f}ms end={rel_end:.0f}ms dur={dur*1000:.0f}ms")
                if dur > args.slow_sec:                         # 느림 경고
                    print(f" ~ 느림 경고: {fp.name} {dur:.2f}s")
                return (fp, h, meta12, dur)                     # 결과 반환
            except Exception as e:
                t_end = time.perf_counter()                     # 끝 시각
                print(f" ! 예외 발생 {fp.name} start={(t_start - t0)*1000:.0f}ms end={(t_end - t0)*1000:.0f}ms err={e}")
                return (fp, h, e, 0.0)                          # 예외 반환

        iterator: Iterable = map(llm_worker, todo) if args.parallel <= 1 \
            else cf.ThreadPoolExecutor(max_workers=args.parallel).map(llm_worker, todo)

        total = len(todo)                                       # 총 개수
        since_commit = 0                                        # 커밋 주기 카운터
        conn.execute("BEGIN")                                   # 트랜잭션 시작
        for i, result in enumerate(iterator, 1):                # 결과 순회
            fp, h, meta_or_exc, dur = result                    # 언팩
            try:
                if isinstance(meta_or_exc, Exception):          # 예외였으면
                    raise meta_or_exc                            # 상위로 던짐
                meta12 = normalize_meta(meta_or_exc)            # 12필드 보정
                (name, summary, detail, tags, archetype,
                 background, scenario, system_prompt, greeting,
                 world, genre, style) = meta12                  # 언팩

                # world/genre/style 비어있으면 보강
                world, genre, style = enrich_world_fields(name, summary, detail, tags, world, genre, style)
                # 이름 보정
                name = coerce_korean_name(name, h)
                # 파일 이동
                dst = move_to_img_by_hash(fp, img_dir, h)
                # DB 행 준비(pending 상태로 표기, meta_version=1)
                row = dict(
                    name=name, summary=summary, detail=detail, tags=tags,
                    image="/assets/char/"+dst.name, img_hash=h,
                    archetype=archetype, background=background, scenario=scenario,
                    system_prompt=system_prompt, greeting=greeting,
                    src_file=fp.name, world=world, genre=genre, style=style,
                    vision_model=args.vision_model or "", polish_model="",
                    polish_status="pending", meta_version=1,
                )
                try:
                    insert_character_row(conn, row)             # 신규 INSERT
                    moved += 1                                  # 카운트
                    print(f" + {i}/{total} 등록: {dst.name} [{name}] ({dur:.2f}s, {dur*1000:.0f}ms)")
                except sqlite3.IntegrityError:                  
                    # 중복 → 정책별 처리
                    if args.on_duplicate == "delete":           # 삭제 정책
                        try:
                            dst.unlink(missing_ok=True)         # 방금 이동한 파일 삭제
                        except Exception:
                            pass
                        deleted += 1                            # 삭제 카운트
                        print(f" - 경합 중복 삭제: {fp.name}")
                    elif args.on_duplicate == "update":         # 업데이트 정책
                        # pending 상태로 갱신
                        conn.execute(
                            """
                            UPDATE characters SET
                                name=?, summary=?, detail=?, tags=?, image=?,
                                updated_at=strftime('%s','now'),
                                archetype=?, background=?, scenario=?, system_prompt=?, greeting=?, src_file=?,
                                world=?, genre=?, style=?,
                                vision_model=?, polish_model=?, polish_status='pending', meta_version=1
                            WHERE img_hash=?
                            """,
                            (
                                row["name"], row["summary"], row["detail"], json.dumps(row["tags"], ensure_ascii=False),
                                row["image"], row["archetype"], row["background"], row["scenario"], row["system_prompt"],
                                row["greeting"], row["src_file"], row["world"], row["genre"], row["style"],
                                row["vision_model"], row["polish_model"], row["img_hash"]
                            ),
                        )
                        print(f" * {i}/{total} 중복→업데이트: {dst.name} [{name}]")
                    else:
                        print(f" - {i}/{total} 중복 스킵: {fp.name}")
                    dup += 1                                    # 중복 카운트
                since_commit += 1                               # 커밋 카운트
                if since_commit >= args.commit_interval:        # 주기 도달 시
                    conn.commit(); since_commit = 0             # 커밋 후 초기화
            except Exception as e:
                fail += 1                                       # 실패 카운트
                print(f" ! 이동/DB 실패 {fp.name}: {e}")        # 로그
        conn.commit()                                           # 마지막 커밋
    except Exception:
        conn.rollback(); raise                                  # 예외 시 롤백/전파
    finally:
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")    # WAL 체크포인트
        except Exception:
            pass
        conn.close()                                            # DB 닫기
        print(f"[TIMING] TOTAL {time.perf_counter()-t0:.2f}s")  # 총 소요 출력

    print(f"[PROC] 완료: 이동 {moved} / 중복 {dup} (삭제 {deleted}) / 실패 {fail}")  # 요약

def run_mode_polish(args):
    """2차 파이프라인: DB pending 집합만 폴리싱 후 UPDATE"""
    conn = sqlite3.connect(args.db)                             # DB 연결
    tune_sqlite(conn, args.busy_timeout)                        # SQLite 튜닝
    ensure_characters_table(conn)                               # 테이블 보장

    batch = max(1, int(args.batch))                             # 배치 크기 보정
    # pending 집합 조회(오래된 순)
    rows = conn.execute(
        """
        SELECT id, name, summary, detail, tags, archetype, background, scenario,
               system_prompt, greeting, world, genre, style, img_hash
        FROM characters
        WHERE polish_status='pending'
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (batch,)
    ).fetchall()

    if not rows:                                                # 없으면 종료
        print("[PROC] 폴리싱 대기 레코드가 없습니다."); conn.close(); return

    print(f"[PROC] 폴리싱 대상 {len(rows)}개")                 # 대상 개수 출력
    t0 = time.perf_counter()                                    # 시작 시각
    ok = fail = 0                                               # 카운터

    for idx, row in enumerate(rows, 1):                         # 각 레코드 순회
        (rid, name, summary, detail, tags_json, archetype, background,
         scenario, system_prompt, greeting, world, genre, style, img_hash) = row
        try:
            tags = json.loads(tags_json) if tags_json else []   # 태그 역직렬화
        except Exception:
            tags = []                                           # 실패 시 빈 리스트

        # world/genre/style 보강
        world, genre, style = enrich_world_fields(name, summary, detail, tags, world, genre, style)

        # 폴리싱 호출
        meta12 = (name, summary, detail, tags, archetype, background, scenario, system_prompt, greeting, world, genre, style)
        meta12 = polish_meta(meta12, args.polish_model)
        # 언팩
        (name, summary, detail, tags, archetype, background, scenario, system_prompt, greeting, world, genre, style) = normalize_meta(meta12)
        # UPDATE
        conn.execute(
            """
            UPDATE characters SET
                name=?, summary=?, detail=?, tags=?, 
                archetype=?, background=?, scenario=?, system_prompt=?, greeting=?,
                world=?, genre=?, style=?,
                polish_model=?, polish_status='done', meta_version=2,
                updated_at=strftime('%s','now')
            WHERE id=?
            """,
            (
                name, summary, detail, json.dumps(tags, ensure_ascii=False),
                archetype, background, scenario, system_prompt, greeting,
                world, genre, style, args.polish_model, rid
            ),
        )
        ok += 1                                                 # 성공 카운트
        print(f" + {idx}/{len(rows)} 폴리싱 완료: #{rid} [{name}]")

    conn.commit()                                               # 커밋
    conn.close()                                                # 닫기
    print(f"[TIMING] TOTAL {time.perf_counter()-t0:.2f}s")      # 총 소요 출력
    print(f"[PROC] 완료: 업데이트 {ok} / 실패 {fail}")           # 요약

# ============================== 메인 엔트리 ================================
def main():
    """CLI 인자 파싱 및 모드별 실행"""
    ap = argparse.ArgumentParser()                              # 파서 생성
    ap.add_argument("--mode", choices=["vision","polish"], default="vision", help="실행 모드 선택")  # 모드
    ap.add_argument("--temp-dir", default="F:/git/ai/apps/web-html/assets/temp", help="임시 이미지 폴더")  # temp
    ap.add_argument("--img-dir",  default="F:/git/ai/apps/web-html/assets/char", help="최종 이미지 폴더")  # img
    ap.add_argument("--db",       default="F:/git/ai/app.sqlite3", help="SQLite DB 경로")  # DB

    ap.add_argument("--model",    default=os.getenv("CRAWLER_OLLAMA_MODEL", "qwen2.5:7b-instruct"), help="텍스트 폴백 모델")  # 텍스트
    ap.add_argument("--vision-model", default=None, help="비전 모델명(예: moondream, llava-phi3)")  # 비전 모델
    ap.add_argument("--polish-model", default="qwen2.5:7b-instruct-q4_K_M", help="폴리싱 텍스트 모델")  # 폴리싱 모델

    ap.add_argument("--query",    default="Pinterest 수집 이미지", help="비전/텍스트 공통 컨텍스트")  # 컨텍스트
    ap.add_argument("--on-duplicate", choices=["delete","skip","update"], default="delete", help="중복 이미지 처리 정책")  # 중복 정책

    ap.add_argument("--max", type=int, default=0, help="(vision) 처리할 최대 파일 수(0=제한없음)")  # 최대 수
    ap.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL, help="(vision) 동시 처리 스레드 수")  # 스레드 수
    ap.add_argument("--commit-interval", type=int, default=1, help="(vision) N개 처리마다 커밋")  # 커밋 간격
    ap.add_argument("--busy-timeout", type=int, default=3000, help="SQLite busy_timeout(ms)")  # busy_timeout
    ap.add_argument("--slow-sec", type=float, default=25.0, help="(vision) 느림 경고 임계값(초)")  # 느림 경고

    ap.add_argument("--batch", type=int, default=50, help="(polish) 한 번에 폴리싱할 레코드 수")  # 배치 크기

    args = ap.parse_args()                                     # 인자 파싱

    if args.mode == "vision":                                  # 1차 모드
        run_mode_vision(args)                                  # 실행
    else:                                                      # 2차 모드
        run_mode_polish(args)                                  # 실행

if __name__ == "__main__":                                     # 스크립트 엔트리
    main()                                                     # 메인 호출
