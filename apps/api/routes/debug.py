from fastapi import APIRouter

import os, certifi
from pymongo import MongoClient

router = APIRouter()

@router.get("/debug/mongo-ping")
def mongo_ping():
    uri = os.environ.get("MONGO_URI", "")
    ok_srv = uri.startswith("mongodb+srv://")
    if not ok_srv:
        return {"ok": False, "reason": "MONGO_URI is not SRV", "uri_prefix": uri.split('@')[0] if uri else ""}
    c = MongoClient(uri, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=15000)
    r = c.admin.command("ping")
    return {"ok": True, "ping": r}

