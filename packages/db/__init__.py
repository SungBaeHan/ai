import os, json, sqlite3, time
from pathlib import Path

# 프로젝트 루트/DB 경로
# ROOT = Path(__file__).resolve().parents[2]  # .../ai
# DATA = ROOT / "data"
# DATA.mkdir(exist_ok=True)
# DB_PATH = DATA / "app.sqlite3"

# 기본 경로: 환경변수(DB_PATH) → 홈디렉토리 ai_db → 기존 data 폴더 순서로 탐색
# DEFAULT_DB = Path("/home/sbhan/ai_db/app.sqlite3")
# ROOT = Path(__file__).resolve().parents[2]  # .../ai
# DATA = ROOT / "data"
# DATA.mkdir(exist_ok=True)

# ✅ DB_PATH 환경변수가 지정되어 있으면 그걸 우선 사용
# DB_PATH = Path(os.getenv("DB_PATH", DEFAULT_DB))
# ✅ 기본값을 윈도우 드라이브 경로로
DB_PATH = Path(os.getenv("DB_PATH", "/mnt/f/git/ai/data/app.sqlite3"))

def get_conn():
    # conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # 🔧 개발 편의 PRAGMA
    try:
        conn.execute("PRAGMA journal_mode=DELETE")  # WAL 끄기 (윈도우 GUI 동시접근 편리)
        conn.execute("PRAGMA synchronous=OFF")      # 디스크 flush 완화 (속도↑, 안정성↓)
        conn.execute("PRAGMA busy_timeout=2000")    # 잠금 시 2초 대기
    except Exception:
        pass
    
    return conn

def init_db():
    with get_conn() as cx:
        cx.execute("""
        CREATE TABLE IF NOT EXISTS characters(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            summary TEXT NOT NULL,
            detail TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            image TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")
        cx.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_char_image ON characters(image)")
        cx.commit()

def upsert_character_by_image(name, summary, detail, tags, image):
    with get_conn() as cx:
        # 있으면 업데이트, 없으면 인서트
        cur = cx.execute("SELECT id FROM characters WHERE image=?", (image,))
        row = cur.fetchone()
        if row:
            cx.execute(
                "UPDATE characters SET name=?, summary=?, detail=?, tags=?, created_at=? WHERE id=?",
                (name, summary, detail, json.dumps(tags, ensure_ascii=False), int(time.time()), row["id"])
            )
        else:
            cx.execute(
                "INSERT INTO characters(name,summary,detail,tags,image,created_at) VALUES(?,?,?,?,?,?)",
                (name, summary, detail, json.dumps(tags, ensure_ascii=False), image, int(time.time()))
            )
        cx.commit()

def insert_character(name:str, summary:str, detail:str, tags:list, image:str):
    with get_conn() as cx:
        cx.execute(
            "INSERT INTO characters(name,summary,detail,tags,image,created_at) VALUES(?,?,?,?,?,?)",
            (name, summary, detail, json.dumps(tags, ensure_ascii=False), image, int(time.time()))
        )
        cx.commit()

def list_characters(offset:int=0, limit:int=30):
    with get_conn() as cx:
        cur = cx.execute(
            "SELECT id,name,summary,detail,tags,image,created_at FROM characters ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if isinstance(r.get("tags"), str):
                try: r["tags"] = json.loads(r["tags"])
                except: r["tags"] = []
        return rows

def count_characters():
    with get_conn() as cx:
        return cx.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
