#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
[2/2] temp 후처리
- temp 폴더의 이미지를 읽어 해시 생성 → DB 중복 검사
- 중복이 아니면 LLM 메타 생성, DB 삽입, img 폴더로 이동(파일명: 해시 기반 고유명)
- 중복이면 삭제 또는 스킵(옵션)

예)
python process_temp_images.py \
  --temp-dir "F:/git/ai/apps/web-html/assets/temp" \
  --img-dir  "F:/git/ai/apps/web-html/assets/img" \
  --db "F:/git/ai/app.sqlite3" \
  --model "qwen2.5:7b-instruct" \
  --query "캐릭터 일러스트 수집" \
  --on-duplicate delete
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ── DB Helpers ───────────────────────────────────────────────
def ensure_characters_table(conn: sqlite3.Connection):
    cur = conn.cursor()
    # 최소 스키마 보장
    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        summary TEXT,
        detail TEXT,
        tags TEXT,           -- JSON 문자열
        image TEXT,          -- /assets/img/xxx.jpg
        img_hash TEXT,
        created_at INTEGER
    )
    """)
    conn.commit()
    # img_hash UNIQUE 인덱스
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_characters_img_hash ON characters(img_hash)")
    conn.commit()

def image_hash_exists(conn: sqlite3.Connection, h: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM characters WHERE img_hash=? LIMIT 1", (h,))
    return cur.fetchone() is not None

def insert_character(conn: sqlite3.Connection, row: Dict[str, Any]):
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
    conn.commit()

# ── LLM 메타 생성 ─────────────────────────────────────────────
def generate_metadata_via_llm(query: str, model: str) -> Tuple[str, str, str, List[str]]:
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model,
            temperature=0.7,
            top_p=0.9,
            num_predict=200,
            num_ctx=2048
        )
        sys = (
            "당신은 TRPG/캐릭터 데이터 디자이너입니다. "
            "짧고 선명한 한국어를 사용하고, 다음 JSON 스키마로만 답하세요. "
            "이름은 1~2어절 한국/일본풍 여성 캐릭터명. "
            "summary는 40~80자, detail은 120~220자. "
            "태그는 2~5개, 한국어 단어들."
        )
        user = f"""
검색 컨텍스트: {query}

JSON만 출력하세요:
{{
  "name": "...",
  "summary": "...",
  "detail": "...",
  "tags": ["...", "..."]
}}
"""
        msg = [{"role":"system","content":sys},{"role":"user","content":user}]
        out = llm.invoke(msg)
        text = out.content if hasattr(out, "content") else str(out)
        data = json.loads(text)
        name    = str(data.get("name","세라"))
        summary = str(data.get("summary","결연한 표정의 모험가."))
        detail  = str(data.get("detail","과거를 감춘 채 유랑 중인 검사. 즉흥적이지만 동료에게 따뜻하다."))
        tags    = data.get("tags", ["TRPG","캐릭터"])
        if not isinstance(tags, list): tags = ["TRPG","캐릭터"]
        return name, summary, detail, tags
    except Exception:
        # 실패 시 짧은 기본값
        return (
            "세라",
            "결연한 표정과 개성적인 분위기의 캐릭터. 탐험과 전투에 능하다.",
            "과거를 감춘 채 유랑 중인 검사. 즉흥적이지만 동료에게는 따뜻하다. 새로운 사건의 냄새를 맡으면 바로 움직인다.",
            ["TRPG","캐릭터"]
        )

# ── 기타 유틸 ────────────────────────────────────────────────
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_ext(p: Path) -> str:
    # 확장자 없는 경우 jpg 기본
    ext = p.suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    return ".jpg"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--temp-dir", default="F:/git/ai/apps/web-html/assets/temp", help="임시 디렉토리")
    ap.add_argument("--img-dir",  default="F:/git/ai/apps/web-html/assets/img",  help="최종 이미지 디렉토리")
    ap.add_argument("--db",       default="F:/git/ai/app.sqlite3", help="SQLite 파일 경로")
    ap.add_argument("--model",    default=os.getenv("CRAWLER_OLLAMA_MODEL","phi3:mini"), help="Ollama 모델명")
    ap.add_argument("--query",    default="Pinterest 수집 이미지", help="LLM 메타 생성 컨텍스트")
    ap.add_argument("--on-duplicate", choices=["delete","skip"], default="delete",
                    help="중복(해시 존재) 시 temp 파일 처리 방식")
    args = ap.parse_args()

    temp_dir = Path(args.temp_dir); temp_dir.mkdir(parents=True, exist_ok=True)
    img_dir  = Path(args.img_dir);  img_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    ensure_characters_table(conn)

    files = [p for p in temp_dir.iterdir() if p.is_file()]
    if not files:
        print("[PROC] 처리할 파일이 없습니다.")
        return

    print(f"[PROC] 대상 {len(files)}개 파일")
    moved = dup = fail = 0

    for i, fp in enumerate(files, 1):
        try:
            h = sha256_file(fp)
            if image_hash_exists(conn, h):
                dup += 1
                if args.on_duplicate == "delete":
                    fp.unlink(missing_ok=True)
                    print(f" - {i}/{len(files)} 중복 → 삭제: {fp.name}")
                else:
                    print(f" - {i}/{len(files)} 중복 → 스킵: {fp.name}")
                continue

            # 메타 생성
            name, summary, detail, tags = generate_metadata_via_llm(args.query, args.model)

            # 최종 파일명: 해시 앞 12자리 + 원본 확장자
            ext = safe_ext(fp)
            final_name = f"{h[:12]}{ext}"
            dst = img_dir / final_name

            # 이동
            shutil.move(str(fp), str(dst))

            # DB 삽입 (웹 경로 표준화)
            rel_web_path = "/assets/img/" + dst.name
            row = dict(
                name=name, summary=summary, detail=detail, tags=tags,
                image=rel_web_path, img_hash=h
            )
            insert_character(conn, row)
            moved += 1
            print(f" + {i}/{len(files)} 이동/등록: {dst.name}  [{name}]")

        except Exception as e:
            fail += 1
            print(f" ! {i}/{len(files)} 실패 {fp.name}: {e}")

    print(f"[PROC] 완료: 이동 {moved} / 중복 {dup} / 실패 {fail}")

if __name__ == "__main__":
    main()
