# ========================================
# apps/api/routes/auth_google.py - Google OAuth 인증 API
# - POST /v1/auth/google: 구글 로그인 처리
#   + MongoDB users 컬렉션과 연동 (get_or_create)
#   + is_use, is_lock, member_level 을 응답으로 반환
# ========================================

import os
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

from adapters.persistence.mongo.factory import get_mongo_client

try:
    import jwt
except ImportError:
    try:
        import PyJWT as jwt
    except ImportError:
        raise ImportError("PyJWT가 설치되지 않았습니다. pip install PyJWT를 실행하세요.")

router = APIRouter()

# 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 60 * 60 * 24 * 7  # 7일

# 구글 토큰 검증 URL
GOOGLE_TOKEN_VERIFY_URL = "https://oauth2.googleapis.com/tokeninfo"




class GoogleLoginRequest(BaseModel):
    token: str  # Google Identity Services에서 받은 JWT 토큰





def verify_google_token(token: str) -> dict:
    """
    Google Identity Services JWT 토큰 검증
    """
    try:
        # Google API로 토큰 검증
        response = requests.get(
            f"{GOOGLE_TOKEN_VERIFY_URL}?id_token={token}",
            timeout=5,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")

        token_info = response.json()

        # 클라이언트 ID 확인 (옵션, 보안 강화)
        if GOOGLE_CLIENT_ID and token_info.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token audience mismatch")

        # 필요한 필드 확인
        if "email" not in token_info or "sub" not in token_info:
            raise HTTPException(status_code=401, detail="Invalid token format")

        return {
            "sub": token_info["sub"],  # Google user ID
            "email": token_info["email"],
            "name": token_info.get("name", token_info.get("email", "User")),
            "picture": token_info.get("picture"),
            "email_verified": token_info.get("email_verified", False),
        }
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Token verification failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")





def create_jwt_token(user_info: dict) -> str:
    """
    사용자 정보로 JWT 토큰 생성
    """
    payload = {
        "sub": user_info["sub"],  # Google user ID
        "email": user_info["email"],
        "name": user_info.get("name"),
        "iat": int(time.time()),  # Issued at
        "exp": int(time.time()) + JWT_EXPIRATION,  # Expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)





def get_or_create_user(user_info: dict) -> dict:
    """
    MongoDB users 컬렉션에서 사용자 조회/생성.
    - 기존: email 또는 google_id(sub)로 조회
    - 없으면 새로 생성 (is_use='N', is_lock='Y', member_level=1 기본)
    """
    db = get_mongo_client()
    users = db.users


    email = user_info["email"]
    google_id = user_info["sub"]
    name = user_info.get("name") or email


    # 기존 유저 조회
    doc = users.find_one({"$or": [{"email": email}, {"google_id": google_id}]})


    now = datetime.utcnow()


    if doc:
        # 이름/이메일 업데이트 + updated_at 갱신 (플래그는 그대로 유지)
        update = {
            "email": email,
            "display_name": name,
            "updated_at": now,
        }
        users.update_one({"_id": doc["_id"]}, {"$set": update})
        doc.update(update)
    else:
        # 새 유저 생성 (기본 플래그: 사용 불가 + 잠금 + 일반유저)
        doc = {
            "email": email,
            "google_id": google_id,
            "display_name": name,
            "is_use": "N",
            "is_lock": "Y",
            "member_level": 1,
            "created_at": now,
            "updated_at": now,
        }
        inserted_id = users.insert_one(doc).inserted_id
        doc["_id"] = inserted_id


    return doc





@router.post("/google")
async def google_login(request: GoogleLoginRequest):
    """
    구글 로그인 처리
    - Google Identity Services에서 받은 token 검증
    - users 컬렉션에서 유저 조회/생성
    - JWT 토큰 + 계정 플래그(is_use, is_lock, member_level) 반환
    """
    try:
        # 1) Google 토큰 검증
        user_info = verify_google_token(request.token)


        # 2) MongoDB users 컬렉션 연동
        user_doc = get_or_create_user(user_info)


        # 3) JWT 토큰 생성
        access_token = create_jwt_token(user_info)


        # 4) 응답 데이터
        return {
            "access_token": access_token,
            "email": user_doc["email"],
            "name": user_doc.get("display_name") or user_info["name"],
            "is_use": user_doc.get("is_use", "N"),
            "is_lock": user_doc.get("is_lock", "Y"),
            "member_level": user_doc.get("member_level", 1),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
