# apps/api/routes/assets.py
from fastapi import APIRouter, Query
from adapters.file_storage.r2_storage import R2Storage

router = APIRouter(prefix="/assets", tags=["assets"])
r2 = R2Storage()

@router.get("/images")
def list_images(
    prefix: str = Query("char/"),
    limit: int = Query(100, ge=1, le=1000),
    signed: bool = Query(True),
):
    keys = r2.list_objects(prefix=prefix, limit=limit)
    if signed:
        items = [{"key": k, "url": r2.get_presigned_url(k)} for k in keys]
    else:
        items = [{"key": k} for k in keys]
    return {"prefix": prefix, "count": len(items), "items": items}
