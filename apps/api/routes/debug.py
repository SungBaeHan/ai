from fastapi import APIRouter

import os, certifi
from pymongo import MongoClient
from apps.api.utils import mask_mongo_uri

router = APIRouter()

@router.get("/debug/mongo-ping")
def mongo_ping():
    uri = os.environ.get("MONGO_URI", "")
    ok_srv = uri.startswith("mongodb+srv://")
    if not ok_srv:
        masked_prefix = mask_mongo_uri(uri.split('@')[0] + "@[redacted]") if uri else ""
        return {"ok": False, "reason": "MONGO_URI is not SRV", "uri_prefix": masked_prefix}
    c = MongoClient(uri, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=15000)
    r = c.admin.command("ping")
    return {"ok": True, "ping": r}

