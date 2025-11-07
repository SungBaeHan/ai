from fastapi import APIRouter
import os

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_root():
    return {"ok": True}


@router.get("/db")
def health_db():
    backend = os.getenv("DATA_BACKEND", "mongo").lower()
    if backend == "mongo":
        try:
            from adapters.persistence.mongo.character_repository_adapter import MongoCharacterRepository
            r = MongoCharacterRepository()
            # 간단 카운트 (샘플)
            n = r.collection.estimated_document_count()
            return {"ok": True, "backend": "mongo", "estimated_count": int(n)}
        except Exception as e:
            return {"ok": False, "backend": "mongo", "error": str(e)}
    else:
        try:
            import sqlite3
            db_path = os.getenv("DB_PATH", "/data/db/app.sqlite3")
            con = sqlite3.connect(db_path); con.close()
            return {"ok": True, "backend": "sqlite", "db_path": db_path}
        except Exception as e:
            return {"ok": False, "backend": "sqlite", "error": str(e)}

