from fastapi import APIRouter
import os

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def root():
    return {"ok": True}


@router.get("/env")
def env_present():
    keys = ["DATA_BACKEND","MONGO_URI","MONGO_DB","R2_ENDPOINT","R2_BUCKET"]
    present = {k: bool(os.getenv(k)) for k in keys}
    return {"ok": True, "present": present}


@router.get("/db")
def db_check():
    backend = (os.getenv("DATA_BACKEND","mongo") or "mongo").lower()
    if backend == "mongo":
        try:
            from adapters.persistence.mongo.character_repository_adapter import MongoCharacterRepository
            r = MongoCharacterRepository()
            r.list_all(limit=1)  # triggers connection
            return {"ok": True, "backend": "mongo"}
        except Exception as e:
            return {"ok": False, "backend": "mongo", "error": str(e)}
    else:
        try:
            import sqlite3
            db_path = os.getenv("DB_PATH","/data/db/app.sqlite3")
            con = sqlite3.connect(db_path); con.close()
            return {"ok": True, "backend": "sqlite"}
        except Exception as e:
            return {"ok": False, "backend": "sqlite", "error": str(e)}

