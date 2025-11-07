from fastapi import FastAPI
import os

app = FastAPI()


@app.get("/diag/ping")
def ping():
    return {"ok": True, "msg": "fallback alive"}


@app.get("/diag/env")
def env():
    keys = ["DATA_BACKEND","MONGO_URI","MONGO_DB","R2_ENDPOINT","R2_BUCKET","PORT","PYTHONPATH"]
    masked = {}
    for k in keys:
        v = os.getenv(k)
        if v is None:
            masked[k] = None
        elif k in ("MONGO_URI",):
            masked[k] = (v[:8] + "...") if len(v or "") > 8 else "***"
        else:
            masked[k] = v
    return {"ok": True, "env": masked}

