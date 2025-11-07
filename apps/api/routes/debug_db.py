from fastapi import APIRouter
import os, sqlite3, json, pathlib, time

router = APIRouter(prefix="/_debug", tags=["debug"])

def _probe_sqlite(db_path: str):
    info = {"db_path": db_path, "exists": False, "size": 0, "open_ok": False, "pragma_user_version": None}
    try:
        p = pathlib.Path(db_path)
        info["exists"] = p.exists()
        if p.exists():
            info["size"] = p.stat().st_size
        con = sqlite3.connect(db_path)
        info["open_ok"] = True
        try:
            cur = con.execute("PRAGMA user_version;")
            row = cur.fetchone()
            info["pragma_user_version"] = row[0] if row else None
        finally:
            con.close()
    except Exception as e:
        info["error"] = str(e)
    return info

@router.get("/db")
def debug_db():
    db_path = os.getenv("DB_PATH", "/data/db/app.sqlite3")
    return {"ts": int(time.time()), "sqlite": _probe_sqlite(db_path)}

