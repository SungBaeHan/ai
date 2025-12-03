# ========================================
# apps/api/routes/auth_google.py - Google OAuth 인증 API
# - POST /v1/auth/google: 구글 로그인 처리
#   + Google 토큰 검증
#   + MongoDB users 컬렉션 연동 (get_or_create)
#   + is_use, is_lock, member_level 플래그 포함해서 응답
# ========================================

import os
import time
from datetime import datetime, timezone
import requests

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from adapters.persistence.mongo.factory import get_mongo_client
from apps.api.core.user_info_token import create_user_info_token

try:
    import jwt
except ImportError:
    try:
        import PyJWT as jwt
    except ImportError:
        raise ImportError("PyJWT 가 설치되지 않았습니다. pip install PyJWT 또는 PyJWT 를 설치하세요.")

router = APIRouter()

# 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 60 * 60 * 24 * 7  # 7일

GOOGLE_TOKEN_VERIFY_URL = "https://oauth2.googleapis.com/tokeninfo"

class GoogleLoginRequest(BaseModel):
    token: str  # Google Identity Services 에서 받은 id_token

def verify_google_token(token: str) -> dict:
    """
    Google Identity Services id_token 검증
    """
    try:
        resp = requests.get(
            f"{GOOGLE_TOKEN_VERIFY_URL}?id_token={token}",
            timeout=5,
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")

        info = resp.json()

        # aud 검사 (옵션이지만 있으면 체크)
        if GOOGLE_CLIENT_ID and info.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token audience mismatch")

        if "email" not in info or "sub" not in info:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {
            "sub": info["sub"],
            "email": info["email"],
            "name": info.get("name", info.get("email", "User")),
            "picture": info.get("picture"),
            "email_verified": info.get("email_verified", False),
        }
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Google verify error: {e}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token parse error: {e}")

def create_jwt_token(user_info: dict) -> str:
    """
    클라이언트에 내려줄 access_token 생성
    (지금은 단순 JWT, 나중에 세션/리프레시 토큰 구조로 확장 가능)
    """
    now = int(time.time())
    payload = {
        "sub": user_info["sub"],
        "email": user_info["email"],
        "name": user_info.get("name"),
        "iat": now,
        "exp": now + JWT_EXPIRATION,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_or_create_user(user_info: dict) -> dict:
    """
    MongoDB users 컬렉션과 연동:
    - email 또는 google_id(sub)로 조회
    - 없으면 새 문서 생성
    - 있으면 email/display_name/updated_at/last_login_at 갱신
    """
    db = get_mongo_client()
    users = db.users

    email = user_info["email"]
    google_id = user_info["sub"]
    name = user_info.get("name") or email

    now = datetime.now(timezone.utc)

    # 기존 유저 조회
    doc = users.find_one({"$or": [{"email": email}, {"google_id": google_id}]})

    if doc:
        update = {
            "email": email,
            "display_name": name,
            "updated_at": now,
            "last_login_at": now,
        }
        users.update_one({"_id": doc["_id"]}, {"$set": update})
        doc.update(update)
    else:
        # 기본 플래그: 사용 불가 + 잠금 + 일반 유저
        doc = {
            "email": email,
            "google_id": google_id,
            "display_name": name,
            "is_use": "N",
            "is_lock": "Y",
            "member_level": 1,
            "created_at": now,
            "updated_at": now,
            "last_login_at": now,
        }
        inserted_id = users.insert_one(doc).inserted_id
        doc["_id"] = inserted_id

    return doc

@router.post("/google")
async def google_login(body: GoogleLoginRequest):
    """
    구글 로그인 엔드포인트
    - 프론트: POST /v1/auth/google { token }
    - 처리:
      1) Google token 검증
      2) users 컬렉션 get_or_create (last_login_at 업데이트)
      3) access_token + user_info_v2 (암호화된 토큰) 반환
    """
    # 1) Google 토큰 검증
    user_info = verify_google_token(body.token)

    # 2) users 컬렉션 동기화 (없으면 생성, last_login_at 업데이트)
    user_doc = get_or_create_user(user_info)

    # 3) access_token 생성
    access_token = create_jwt_token(user_info)

    # 4) user_info_v2 토큰 생성 (암호화된 토큰)
    last_login_at = user_doc.get("last_login_at")
    if isinstance(last_login_at, datetime):
        # MongoDB에서 가져온 datetime이 timezone 정보가 없을 수 있으므로 UTC로 변환
        if last_login_at.tzinfo is None:
            last_login_at = last_login_at.replace(tzinfo=timezone.utc)
    else:
        last_login_at = datetime.now(timezone.utc)

    user_info_v2 = create_user_info_token(
        user_id=str(user_doc["_id"]),
        email=user_doc["email"],
        display_name=user_doc.get("display_name") or user_info["name"],
        member_level=user_doc.get("member_level", 1),
        last_login_at=last_login_at,
    )

    # 5) 응답: access_token과 암호화된 user_info_v2만 반환
    return {
        "access_token": access_token,
        "user_info_v2": user_info_v2,
    }
