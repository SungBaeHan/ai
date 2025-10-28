# packages/db/__init__.py
# ------------------------------------------------------------
# SQLite 접속/초기화 + 캐릭터 CRUD 헬퍼 모음
# - get_character_by_id() 추가
# - list_characters()가 JSON tags를 올바르게 파싱하도록 수정
# - 테이블 없으면 생성 + 인덱스 보강
# ------------------------------------------------------------

import os, json, sqlite3, time                           # 표준 라이브러리 임포트
from pathlib import Path                                 # 경로 유틸
from typing import List, Dict, Any, Optional             # 타입 힌트

# DB 파일 경로 (환경변수 DB_PATH 없으면 기본값 사용)
DB_PATH = Path(os.getenv("DB_PATH", "/mnt/f/git/ai/data/app.sqlite3"))

def get_conn() -> sqlite3.Connection:
    """SQLite 연결 생성 (row_factory를 Row로 설정)"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)  # 멀티스레드 안전 X → False
    conn.row_factory = sqlite3.Row                                 # dict처럼 접근 가능하게
    try:
        # 퍼포먼스/락 회피용 pragma (로컬 개발 기준)
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA busy_timeout=2000")
    except Exception:
        pass
    return conn

def init_db() -> None:
    """테이블/인덱스 없으면 생성 (마이그레이션 포함)"""
    with get_conn() as cx:
        cx.execute("""
        CREATE TABLE IF NOT EXISTS characters(
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 숫자 PK (상세조회에 사용)
            name TEXT NOT NULL,                     -- 캐릭터 이름
            summary TEXT NOT NULL,                  -- 한 줄 소개
            detail TEXT DEFAULT '',                 -- 상세 설명
            tags TEXT DEFAULT '[]',                 -- 태그(JSON 문자열)
            image TEXT NOT NULL,                    -- 이미지 경로(/assets/..)
            created_at INTEGER NOT NULL,            -- 생성 시각(epoch)
            archetype TEXT,                         -- 아키타입(선택)
            background TEXT,                        -- 배경(선택)
            scenario TEXT,                          -- 도입 씬(선택)
            system_prompt TEXT,                     -- 캐릭터 프롬프트 규칙(선택)
            greeting TEXT,                          -- 첫 인사/상황(선택)
            -- ↓ 확장 필드
            world TEXT,
            genre TEXT,
            style TEXT,
            img_hash TEXT,
            src_file TEXT
        )""")
        # 누락 컬럼 마이그레이션 (이미 있으면 에러 → 무시)
        for col in ("world","genre","style","img_hash","src_file"):
            try:
                cx.execute(f"ALTER TABLE characters ADD COLUMN {col} TEXT")
            except Exception:
                pass
        # 중복 방지/조회 성능 인덱스
        cx.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_char_image ON characters(image)")
        cx.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_characters_img_hash ON characters(img_hash)")
        cx.commit()

def _fix_tags(v: Any) -> List[str]:
    """tags 컬럼을 파싱해서 항상 리스트로 반환"""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    s = str(v).strip()
    # JSON이면 로드, 아니면 콤마 분리
    if s.startswith("[") or s.startswith("{"):
        try: return json.loads(s)
        except Exception: return []
    return [x.strip() for x in s.split(",") if x.strip()]

def upsert_character_by_image(
    name, summary, detail, tags, image,
    archetype=None, background=None, scenario=None,
    system_prompt=None, greeting=None,
    world=None, genre=None, style=None,
    img_hash=None, src_file=None
) -> None:
    """이미지 경로로 upsert (수집 파이프라인에서 사용)"""
    with get_conn() as cx:
        row = cx.execute("SELECT id FROM characters WHERE image=?", (image,)).fetchone()
        now = int(time.time())
        tags_json = json.dumps(tags, ensure_ascii=False)
        if row:
            cx.execute("""
              UPDATE characters
              SET name=?, summary=?, detail=?, tags=?, created_at=?,
                  archetype=?, background=?, scenario=?, system_prompt=?, greeting=?,
                  world=?, genre=?, style=?, img_hash=?, src_file=?
              WHERE id=?""",
              (name, summary, detail, tags_json, now,
               archetype, background, scenario, system_prompt, greeting,
               world, genre, style, img_hash, src_file, row["id"])
            )
        else:
            cx.execute("""
              INSERT INTO characters
              (name,summary,detail,tags,image,created_at,
               archetype,background,scenario,system_prompt,greeting,
               world,genre,style,img_hash,src_file)
              VALUES(?,?,?,?,?,?,
                     ?,?,?,?,?, ?,?,?,?,?)""",
              (name, summary, detail, tags_json, image, now,
               archetype, background, scenario, system_prompt, greeting,
               world, genre, style, img_hash, src_file)
            )
        cx.commit()

def insert_character(name: str, summary: str, detail: str, tags: list, image: str) -> None:
    """간단 삽입 (관리 도구 등에서 사용)"""
    with get_conn() as cx:
        cx.execute(
            "INSERT INTO characters(name,summary,detail,tags,image,created_at) VALUES(?,?,?,?,?,?)",
            (name, summary, detail, json.dumps(tags, ensure_ascii=False), image, int(time.time()))
        )
        cx.commit()

def list_characters(offset: int = 0, limit: int = 30) -> List[Dict[str, Any]]:
    """목록 조회 (home.html이 사용)"""
    with get_conn() as cx:
        rows = cx.execute("""
            SELECT id, name, summary, detail, image, tags,
                   archetype, background, scenario, system_prompt, greeting,
                   world, genre, style
            FROM characters
            ORDER BY id
            LIMIT ? OFFSET ?""", (limit, offset)
        ).fetchall()
    items: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["tags"] = _fix_tags(d.get("tags"))
        items.append(d)
    return items

def get_character_by_id(char_id: int) -> Optional[Dict[str, Any]]:
    """단일 조회 (chat.html이 사용)"""
    with get_conn() as cx:
        row = cx.execute("""
            SELECT id, name, summary, detail, image, tags,
                   archetype, background, scenario, system_prompt, greeting,
                   world, genre, style
            FROM characters
            WHERE id=?""", (char_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["tags"] = _fix_tags(d.get("tags"))
    return d

def count_characters() -> int:
    """총 캐릭터 수"""
    with get_conn() as cx:
        return cx.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
