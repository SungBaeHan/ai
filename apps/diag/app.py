from fastapi import FastAPI
import os

app = FastAPI()


@app.get("/diag/ping")
def ping():
    return {"ok": True, "msg": "fallback alive"}


@app.get("/diag/env")
def env():
    keys = ["DATA_BACKEND","MONGO_URI","MONGO_DB","R2_ENDPOINT","R2_BUCKET","PYTHONPATH","PORT"]
    masked = {}
    for k in keys:
        v = os.getenv(k)
        if v is None:
            masked[k] = None
        elif k in ("MONGO_URI","R2_SECRET_ACCESS_KEY"):
            masked[k] = v[:8] + "..." if len(v) > 8 else "***"
        else:
            masked[k] = v
    return {"ok": True, "env": masked}

