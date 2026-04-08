"""
My List / My Create 전용 캐릭터 목록 API.

- GET /api/my/characters
- GET /api/my-create/characters
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

from adapters.persistence.mongo import get_db
from apps.api.deps.auth import get_current_user_from_token
from apps.api.utils.common import build_public_image_url

router = APIRouter()


def _normalize_image(path: str | None) -> str | None:
    """저장된 이미지 경로를 public URL로 정규화한다."""
    return build_public_image_url(path)


def _build_my_characters(
    *,
    db,
    current_user: dict,
    skip: int,
    limit: int,
    q: str | None,
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")

    try:
        creator_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")

    filter_query = {"creator": creator_id}
    if q:
        filter_query = {
            "$and": [
                {"creator": creator_id},
                {
                    "$or": [
                        {"name": {"$regex": q, "$options": "i"}},
                        {"tags": {"$regex": q, "$options": "i"}},
                        {"summary": {"$regex": q, "$options": "i"}},
                    ]
                },
            ]
        }

    cursor = (
        db.characters.find(filter_query)
        .sort([("created_at", -1), ("id", -1)])
        .skip(skip)
        .limit(limit)
    )

    items = []
    for doc in cursor:
        doc.pop("_id", None)
        doc["image"] = _normalize_image(doc.get("image"))
        if "creator" in doc and doc["creator"] is not None:
            doc["creator"] = str(doc["creator"])
        if "summary" in doc and "shortBio" not in doc:
            doc["shortBio"] = doc["summary"]
        if "detail" in doc and "longBio" not in doc:
            doc["longBio"] = doc["detail"]
        items.append(doc)

    total = db.characters.count_documents(filter_query)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/my/characters", summary="My List: 내가 만든 캐릭터 목록")
def get_my_characters_for_my_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    q: str | None = Query(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return _build_my_characters(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        q=q,
    )


@router.get("/my-create/characters", summary="My Create: 내가 만든 캐릭터 목록")
def get_my_characters_for_my_create(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    q: str | None = Query(None),
    db=Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return _build_my_characters(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        q=q,
    )

