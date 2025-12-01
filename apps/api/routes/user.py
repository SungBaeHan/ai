from datetime import datetime

from bson import ObjectId

from fastapi import APIRouter, HTTPException, status

from adapters.persistence.mongo.factory import get_mongo_client

from apps.api.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["users"])

def _doc_to_user_out(doc: dict) -> UserOut:

    return UserOut(

        id=str(doc["_id"]),

        email=doc["email"],

        google_id=doc["google_id"],

        display_name=doc["display_name"],

        is_use=doc.get("is_use", "N"),

        is_lock=doc.get("is_lock", "Y"),

        member_level=doc.get("member_level", 1),

        created_at=doc.get("created_at"),

        updated_at=doc.get("updated_at"),

    )

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)

def create_user(payload: UserCreate):

    db = get_mongo_client()

    users = db.users

    # email, google_id 중복 확인

    exists = users.find_one({

        "$or": [{"email": payload.email}, {"google_id": payload.google_id}]

    })

    if exists:

        raise HTTPException(

            status_code=409,

            detail="이미 동일한 email 또는 google_id가 존재합니다."

        )

    now = datetime.utcnow()

    doc = payload.dict()

    doc["created_at"] = now

    doc["updated_at"] = now

    inserted_id = users.insert_one(doc).inserted_id

    doc["_id"] = inserted_id

    return _doc_to_user_out(doc)

@router.get("/{user_id}", response_model=UserOut)

def get_user(user_id: str):

    db = get_mongo_client()

    users = db.users

    try:

        oid = ObjectId(user_id)

    except:

        raise HTTPException(status_code=400, detail="잘못된 user_id 형식입니다.")

    doc = users.find_one({"_id": oid})

    if not doc:

        raise HTTPException(status_code=404, detail="유저 없음")

    return _doc_to_user_out(doc)

@router.patch("/{user_id}", response_model=UserOut)

def update_user(user_id: str, payload: UserUpdate):

    db = get_mongo_client()

    users = db.users

    try:

        oid = ObjectId(user_id)

    except:

        raise HTTPException(status_code=400, detail="잘못된 user_id 형식입니다.")

    doc = users.find_one({"_id": oid})

    if not doc:

        raise HTTPException(404, detail="유저 없음")

    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items()}

    update_data["updated_at"] = datetime.utcnow()

    users.update_one({"_id": oid}, {"$set": update_data})

    doc.update(update_data)

    return _doc_to_user_out(doc)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)

def delete_user(user_id: str):

    db = get_mongo_client()

    users = db.users

    try:

        oid = ObjectId(user_id)

    except:

        raise HTTPException(400, detail="잘못된 user_id 형식")

    deleted = users.delete_one({"_id": oid})

    if deleted.deleted_count == 0:

        raise HTTPException(404, detail="유저 없음")

    return None

