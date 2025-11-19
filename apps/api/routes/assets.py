# apps/api/routes/assets.py
"""
Assets API - 이미지 메타데이터 조회
MongoDB에서 이미지 메타데이터를 조회하여 반환합니다.
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from adapters.persistence.mongo import get_db
from apps.api.utils import build_public_image_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assets", tags=["assets"])

# ---- Pydantic response models ----

class ImageItem(BaseModel):
    key: str
    url: str

class ImageListResponse(BaseModel):
    items: List[ImageItem]
    total: int

# ---- /assets/images endpoint ----

@router.get("/images", response_model=ImageListResponse, summary="List Images")
def list_images(
    prefix: Optional[str] = Query(default=None, description="R2 key prefix, e.g. 'char/'"),
    limit: int = Query(default=60, ge=1, le=1000),
    signed: bool = Query(default=True, description="Currently ignored; public URLs are returned"),
):
    """
    List image metadata filtered by prefix.

    - Does NOT return 404 when there are no images.
      It returns {"items": [], "total": 0} with status 200.
    - If an unexpected error happens, log it and return 500.
    """
    try:
        db = get_db()
        col_name = os.getenv("MONGO_IMAGES_COLLECTION", "images")
        col = db[col_name]
        
        query: dict = {}
        if prefix:
            # assume "key" field contains the R2 object key
            query["key"] = {"$regex": f"^{prefix}"}
        
        # MongoDB 쿼리 실행
        cursor = col.find(query).sort("key", 1).limit(limit)
        docs = list(cursor)
        
    except Exception as exc:
        logger.exception("Failed to list images from MongoDB: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch images")
    
    items: List[ImageItem] = []
    for doc in docs:
        key = str(doc.get("key", ""))
        if not key:
            continue
        
        # Prefer existing URL in document if present
        url = str(doc.get("url") or doc.get("public_url") or "")
        
        # If there is no URL field, build it from R2_PUBLIC_BASE_URL using common utility
        if not url:
            url = build_public_image_url(key)
            if not url:
                # Cannot build a valid URL without base; skip, but log once
                logger.warning("Missing R2_PUBLIC_BASE_URL; cannot build URL for key=%s", key)
                continue
        
        items.append(ImageItem(key=key, url=url))
    
    return ImageListResponse(items=items, total=len(items))
