#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
temp 후처리(안정판)
- temp 폴더 → 파일 해시 계산(1MB 청크)
- DB에서 해시 중복 선필터(중복이면 delete/skip)
- 남은 파일만 LLM 메타 생성(타임아웃+재시도)
- img 폴더로 해시 기반 고유명 이동 + DB 삽입
- 성능: BEGIN~COMMIT 단일 커밋, WAL/NORMAL PRAGMA, 간단 타이밍 로그
"""
import base64, re, requests   # ← 추가
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import concurrent.futures as cf

# ── 환경 기본값(필요시 환경변수로 조절) ─────────────────────────
LLM_TIMEOUT_SEC = int(os.getenv("META_TIMEOUT_SEC", "25"))   # LLM 응답 타임아웃(초)
LLM_RETRIES     = int(os.getenv("META_RETRIES", "2"))        # 재시도 횟수(총 시도는 1+RETRIES)
LLM_BACKOFF     = float(os.getenv("META_BACKOFF", "1.6"))    # 백오프 배수(1.6배씩 증가)
LLM_MAX_NEW     = int(os.getenv("META_MAX_NEW", "120"))      # 생성 토큰 상한(num_predict)
META_PARALLEL   = int(os.getenv("META_PARALLEL", "1"))       # LLM 병렬 수(1이면 직렬)

# ── DB Helpers ───────────────────────────────────────────────
def ensure_characters_table(conn: sqlite3.Connection) -> None:
    """characters 테이블/인덱스 보장."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        summary TEXT,
        detail TEXT,
        tags TEXT,
        image TEXT,
        img_hash TEXT,
        created_at INTEGER
    )
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_characters_img_hash ON characters(img_hash)")
    conn.commit()

def image_hash_exists(conn: sqlite3.Connection, h: str) -> bool:
    """해시 중복 여부."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM characters WHERE img_hash=? LIMIT 1", (h,))
    return cur.fetchone() is not None

def insert_character_row(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    """캐릭터 레코드 삽입(커밋은 호출부에서 일괄)."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO characters (name, summary, detail, tags, image, img_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["name"],
            row["summary"],
            row["detail"],
            json.dumps(row["tags"], ensure_ascii=False),
            row["image"],
            row["img_hash"],
            int(time.time()),
        ),
    )

# ── LLM 호출(타임아웃+재시도) ─────────────────────────────────
def _llm_once(query: str, model_name: str, image_name: str) -> Tuple[str, str, str, List[str]]:
    """LLM 1회 호출(예외는 상위에서 처리)."""
    try:
        from langchain_ollama import ChatOllama
    except Exception:
        from langchain_community.chat_models import ChatOllama

    llm = ChatOllama(
        model=model_name,
        temperature=0.7,
        model_kwargs={
            "num_predict": LLM_MAX_NEW,
            "repeat_penalty": 1.2,
        },
        # base_url="http://127.0.0.1:11434",  # 필요 시 명시
    )

    sys = """
        당신은 캐릭터의 외형과 분위기를 묘사하는 한국어 작가입니다.
        반드시 JSON 형태로 출력하세요. 예시는 다음과 같습니다.
        {
        "name": "세라",
        "summary": "밝고 쾌활한 검사.",
        "detail": "활기차고 긍정적인 성격의 전사로, 새로운 모험을 두려워하지 않는다.",
        "tags": ["모험", "검사", "여성"]
        }
    """
    user = f"""
검색 컨텍스트: {query}
이미지 파일명: {image_name}

JSON만 출력:
{{
  "name": "...",
  "summary": "...",
  "detail": "...",
  "tags": ["...", "..."]
}}
""".strip()

    msg = [{"role": "system", "content": sys}, {"role": "user", "content": user}]
    out = llm.invoke(msg)
    text = out.content if hasattr(out, "content") else str(out)

    try:
        data = json.loads(text)
    except Exception:
        # JSON이 아닐 경우, 텍스트에서 간략히 추출
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        joined = " ".join(lines)
        name = lines[0][:10] if lines else "이름미상"
        summary = joined[:60] + "..." if len(joined) > 60 else joined
        detail = joined[:200] + "..." if len(joined) > 200 else joined
        tags = ["캐릭터", "일러스트"]
    return name, summary, detail, tags

def call_llm_with_timeout(query: str, model_name: str, image_name: str) -> Tuple[str, str, str, List[str]]:
    """타임아웃+재시도. 끝내 실패하면 안전한 폴백."""
    attempt = 0
    delay = 0.2
    while True:
        attempt += 1
        try:
            with cf.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_llm_once, query, model_name, image_name)
                return fut.result(timeout=LLM_TIMEOUT_SEC)
        except Exception:
            if attempt > LLM_RETRIES + 1:
                base = os.path.splitext(os.path.basename(image_name))[0]
                return (base, "수려한 외모의 모험가.", "자신만의 길을 걷는 인물로, 내면에 깊은 사연을 품고 있다.", ["캐릭터", "일러스트", "모험", "여성"])
            time.sleep(delay)
            delay *= LLM_BACKOFF

# ── 파일/해시 유틸 ───────────────────────────────────────────
def sha256_file(p: Path) -> str:
    """1MB 청크 SHA-256."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_ext(p: Path) -> str:
    """허용 확장자 외에는 .jpg로."""
    ext = p.suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    return ".jpg"

def move_to_img_by_hash(src: Path, img_dir: Path, h: str) -> Path:
    """해시 앞 12자리 + 확장자 파일명으로 img_dir 이동."""
    ext = safe_ext(src)
    final_name = f"{h[:12]}{ext}"
    dst = img_dir / final_name
    shutil.move(str(src), str(dst))
    return dst

# ── 비전용 헬퍼 ──────────────────────────────────────────────

def _extract_json_block(text: str) -> dict:
    """응답 안에 설명 문구가 섞여도 JSON 블록만 추출해서 파싱."""
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{[\s\S]*\}', text)
        if not m:
            raise ValueError("no JSON found")
        return json.loads(m.group(0))

def vision_meta_via_ollama(image_path: str, model_name: str, query: str) -> tuple[str, str, str, list[str]]:
    """Ollama 비전 모델(예: llava:7b, moondream)로 이미지 보고 메타 생성 (Ollama /api/chat 정식 포맷)."""
    import base64, re, requests, os, json

    # 1) 이미지 base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    # 2) 프롬프트
    sys = (
        "너는 캐릭터 일러스트를 분석해 메타데이터를 작성하는 한국어 작가다. "
        "이미지를 보고 반드시 JSON만 출력하라. "
        "name은 1~2어절 한국/일본풍 이름, summary는 1문장(40~80자), "
        "detail은 3~4문장(120~220자), tags는 4~6개 한국어 단어."
    )
    user = f"""검색 컨텍스트: {query}
    이 이미지를 보고 아래 JSON 스키마로 작성하라.
    {{
    "name": "이름",
    "summary": "요약",
    "detail": "상세",
    "tags": ["태그1","태그2","태그3","태그4"]
    }}"""

    # 3) Ollama 멀티모달 채팅 포맷: message에 content=텍스트, images=[base64]
    payload = {
        "model": model_name,  # "llava:7b" 또는 "moondream"
        "stream": False,      # 파싱 편의상 비스트리밍
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user",   "content": user, "images": [b64]},
        ],
        "options": {
            "temperature": 0.7,
            "num_predict": int(os.getenv("META_MAX_NEW", "120")),
            "repeat_penalty": 1.2,
        },
    }

    r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    text = data.get("message", {}).get("content", "")

    # 4) JSON 블록만 추출/파싱 (수다 섞여도 안전)
    def _extract_json_block(text: str) -> dict:
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r'\{[\s\S]*\}', text)
            if not m:
                raise ValueError("no JSON found")
            return json.loads(m.group(0))

    try:
        obj = _extract_json_block(text)
        name    = str(obj.get("name",    "세라")).strip()
        summary = str(obj.get("summary", "밝고 당찬 모험가.")).strip()
        detail  = str(obj.get("detail",  "과거를 감춘 채 방랑하는 전사.")).strip()
        tags    = obj.get("tags", ["캐릭터","일러스트","모험","여성"])
        if not isinstance(tags, list):
            tags = ["캐릭터","일러스트","모험","여성"]
    except Exception:
        base = os.path.splitext(os.path.basename(image_path))[0]
        name, summary, detail, tags = base, "매혹적인 모험가.", "자신만의 길을 걷는 인물로, 내면에 깊은 사연을 품고 있다.", ["캐릭터","일러스트","모험","여성"]

    if len(name) > 8:
        name = name[:8]
    return name, summary, detail, tags

# ── 메인 ─────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--temp-dir", default="F:/git/ai/apps/web-html/assets/temp", help="임시 디렉토리")
    ap.add_argument("--img-dir",  default="F:/git/ai/apps/web-html/assets/img",  help="최종 이미지 디렉토리")
    ap.add_argument("--db",       default="F:/git/ai/app.sqlite3", help="SQLite 파일 경로")
    ap.add_argument("--model",    default=os.getenv("CRAWLER_OLLAMA_MODEL", "phi3:mini"), help="Ollama 모델명")
    ap.add_argument("--query",    default="Pinterest 수집 이미지", help="LLM 메타 생성 컨텍스트")
    ap.add_argument("--on-duplicate", choices=["delete", "skip"], default="delete", help="중복(해시 존재) 시 temp 파일 처리 방식")
    ap.add_argument("--vision-model", default=None, help="Ollama 비전 모델명 (예: llava:7b, moondream)")

    args = ap.parse_args()

    temp_dir = Path(args.temp_dir); temp_dir.mkdir(parents=True, exist_ok=True)
    img_dir  = Path(args.img_dir);  img_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    ensure_characters_table(conn)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # 1) 처리 대상 수집
    files = [p for p in temp_dir.iterdir() if p.is_file()]
    if not files:
        print("[PROC] 처리할 파일이 없습니다.")
        conn.close()
        return
    print(f"[PROC] 대상 {len(files)}개 파일")

    moved = dup = fail = 0
    t_total = time.perf_counter()
    try:
        conn.execute("BEGIN")

        # 2) 사전 단계: 해시 계산 + 중복 선필터 (DB는 메인 스레드에서만!)
        todo: List[Tuple[Path, str]] = []
        for fp in files:
            try:
                h = sha256_file(fp)
                if image_hash_exists(conn, h):
                    dup += 1
                    if args.on_duplicate == "delete":
                        fp.unlink(missing_ok=True)
                        print(f" - 중복 → 삭제: {fp.name}")
                    else:
                        print(f" - 중복 → 스킵: {fp.name}")
                    continue
                todo.append((fp, h))
            except Exception as e:
                fail += 1
                print(f" ! 해시/중복체크 실패 {fp.name}: {e}")

        if not todo:
            conn.commit()
            print(f"[TIMING] TOTAL: {time.perf_counter()-t_total:.2f}s")
            print(f"[PROC] 완료: 이동 {moved} / 중복 {dup} / 실패 {fail}")
            return

        # 3) LLM 단계: 워커는 오직 LLM만(파일/DB 접근 금지)
        def llm_worker(task: tuple[Path, str]) -> tuple[Path, str, tuple[str,str,str,list[str]]]:
            fp, h = task
            t_llm = time.perf_counter()
            if args.vision_model:  # ★ 비전 모델이 지정되면 이미지를 실제로 본다
                meta = vision_meta_via_ollama(str(fp), args.vision_model, args.query)
            else:
                meta = call_llm_with_timeout(args.query, args.model, fp.name)
            print(f"   [TIMING] LLM {fp.name}: {time.perf_counter()-t_llm:.2f}s")
            return (fp, h, meta)

        if META_PARALLEL > 1:
            executor = cf.ThreadPoolExecutor(max_workers=META_PARALLEL)
            results_iter = executor.map(llm_worker, todo)
        else:
            # 직렬로 안전하게
            results_iter = map(llm_worker, todo)

        # 4) 후처리: 파일 이동 + DB 삽입(메인 스레드)
        total_tasks = len(todo)
        for i, (fp, h, meta) in enumerate(results_iter, 1):
            try:
                t_db = time.perf_counter()
                dst = move_to_img_by_hash(fp, img_dir, h)
                name, summary, detail, tags = meta
                rel_web_path = "/assets/img/" + dst.name
                row = dict(name=name, summary=summary, detail=detail, tags=tags,
                           image=rel_web_path, img_hash=h)
                insert_character_row(conn, row)
                moved += 1
                print(f" + {i}/{total_tasks} 이동/등록: {dst.name} [{name}] (DB:{time.perf_counter()-t_db:.2f}s)")
            except Exception as e:
                fail += 1
                print(f" ! 이동/DB 실패 {fp.name}: {e}")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        print(f"[TIMING] TOTAL: {time.perf_counter()-t_total:.2f}s")

    print(f"[PROC] 완료: 이동 {moved} / 중복 {dup} / 실패 {fail}")

if __name__ == "__main__":
    main()
