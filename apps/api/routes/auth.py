# ========================================
# apps/api/routes/auth.py - 인증 API
# - GET /v1/auth/me: 현재 사용자 정보
# - POST /v1/auth/logout: 로그아웃 (토큰 무효화)
# 주의: /v1/auth/google은 auth_google.py에서 처리합니다.
# ========================================

import os
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from bson import ObjectId

from adapters.persistence.mongo.factory import get_mongo_client
from apps.api.core.user_info_token import decode_user_info_token
from apps.api.schemas.user_session import SessionValidateRequest, SessionValidateResponse

try:
    import jwt
except ImportError:
    try:
        import PyJWT as jwt
    except ImportError:
        raise ImportError("PyJWT가 설치되지 않았습니다. pip install PyJWT를 실행하세요.")

router = APIRouter()

# 환경 변수
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")  # TODO: 실제 프로덕션에서는 안전한 시크릿 사용
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 60 * 60 * 24 * 7  # 7일

# 구글 토큰 검증 URL
GOOGLE_TOKEN_VERIFY_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_google_token(credential: str) -> dict:
    """
    Google Identity Services JWT 토큰 검증
    """
    try:
        # Google 공개키를 사용한 검증 (실제로는 google-auth 라이브러리 사용 권장)
        # 간단한 구현을 위해 토큰 정보를 Google API로 확인
        response = requests.get(
            f"{GOOGLE_TOKEN_VERIFY_URL}?id_token={credential}",
            timeout=5
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        token_info = response.json()
        
        # 필요한 필드 확인
        if 'email' not in token_info or 'sub' not in token_info:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        return {
            'sub': token_info['sub'],  # Google user ID
            'email': token_info['email'],
            'name': token_info.get('name', token_info.get('email', 'User')),
            'picture': token_info.get('picture'),
            'email_verified': token_info.get('email_verified', False)
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def create_jwt_token(user_info: dict) -> str:
    """
    사용자 정보로 JWT 토큰 생성
    """
    payload = {
        'sub': user_info['sub'],  # Google user ID
        'email': user_info['email'],
        'name': user_info.get('name'),
        'iat': int(time.time()),  # Issued at
        'exp': int(time.time()) + JWT_EXPIRATION  # Expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 디코드 및 검증
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user_dependency(request: Request):
    """
    FastAPI 의존성 함수: Authorization 헤더에서 JWT 토큰을 읽어서 사용자 정보를 반환.
    MongoDB users 컬렉션에서 user_id를 조회하여 반환.
    """
    # Authorization 헤더에서 토큰 추출
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # JWT의 sub (Google user ID)로 MongoDB에서 user 조회
    db = get_mongo_client()
    users = db.users
    
    google_id = payload.get('sub')
    if not google_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # google_id 또는 email로 user 조회
    user = users.find_one({
        "$or": [
            {"google_id": google_id},
            {"email": payload.get('email')}
        ]
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        'user_id': str(user['_id']),  # MongoDB ObjectId를 문자열로 변환
        'sub': google_id,
        'email': user.get('email', payload.get('email')),
        'name': user.get('display_name', payload.get('name')),
        'member_level': user.get('member_level', 1),
        'is_use': user.get('is_use', 'Y') == 'Y',
        'is_lock': user.get('is_lock', 'N') == 'Y',
    }


@router.get("/me")
async def get_current_user(req: Request):
    """
    현재 로그인한 사용자 정보 조회
    """
    return get_current_user_dependency(req)


@router.post("/logout")
async def logout():
    """
    로그아웃 (클라이언트에서 토큰 삭제 처리, 서버에서는 토큰 무효화 목록 관리 가능)
    """
    # 실제로는 토큰 무효화 목록(블랙리스트)에 추가하거나,
    # 짧은 만료 시간으로 인해 클라이언트에서만 삭제해도 됨
    return {"message": "Logged out successfully"}


@router.post("/validate-session", response_model=SessionValidateResponse)
async def validate_session(request: Request, payload: Optional[SessionValidateRequest] = None):
    """
    로컬스토리지에 저장된 user_info_v2 토큰을 검증하고
    is_use / is_lock / member_level 정보를 반환한다.
    
    토큰은 다음 순서로 찾습니다:
    1. Request에서 extract_token() 사용 (헤더/쿠키)
    2. Body의 token 필드 (하위 호환)
    """
    from apps.api.deps.auth import get_current_user_from_token
    
    # 1) Request에서 토큰 추출 시도
    token = None
    try:
        from apps.api.utils.auth_token import extract_token
        token = extract_token(request)
    except HTTPException:
        # Request에서 토큰을 찾지 못한 경우 body에서 시도
        pass
    
    # 2) Body에서 토큰 추출 (하위 호환)
    if not token and payload and payload.token:
        token = payload.token
        logger.info(
            "[AUTH][TOKEN] source=body len=%d prefix=%s",
            len(token),
            token[:8] if len(token) >= 8 else token,
        )
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # get_current_user_from_token을 사용하여 사용자 정보 가져오기
    # 하지만 이 함수는 Request를 받으므로, 임시 Request 객체를 만들거나
    # 직접 검증 로직을 호출해야 함
    # 대신 get_current_user_from_token의 검증 로직을 재사용
    try:
        user_info = get_current_user_from_token(request)
    except HTTPException:
        # Request에서 추출한 토큰이 실패한 경우, body token으로 직접 검증
        # 이 경우 validate-session의 기존 로직을 사용
        try:
            info = decode_user_info_token(token)
        except ValueError:
            raise HTTPException(status_code=401, detail="invalid_token")

        now = datetime.now(timezone.utc)
        if info.expired_at < now:
            raise HTTPException(status_code=401, detail="token_expired")

        db = get_mongo_client()
        users = db.users

        try:
            user = users.find_one({"_id": ObjectId(info.user_id)})
        except Exception:
            raise HTTPException(status_code=401, detail="invalid_user_id")

        if not user:
            raise HTTPException(status_code=401, detail="user_not_found")

        # last_login_at 이 DB 값과 다르면, 이전 세션 토큰 → 무효
        db_last_login = user.get("last_login_at")
        if db_last_login is None:
            raise HTTPException(status_code=401, detail="session_invalidated")

        # timezone 정보가 없으면 UTC로 가정
        if isinstance(db_last_login, datetime):
            if db_last_login.tzinfo is None:
                db_last_login = db_last_login.replace(tzinfo=timezone.utc)
        else:
            raise HTTPException(status_code=401, detail="session_invalidated")

        # last_login_at 비교 (마이크로초 단위 차이 무시)
        if db_last_login.replace(microsecond=0) != info.last_login_at.replace(microsecond=0):
            raise HTTPException(status_code=401, detail="session_invalidated")

        return SessionValidateResponse(
            ok=True,
            user_id=str(user["_id"]),
            email=user.get("email", info.email),
            display_name=user.get("display_name", info.display_name),
            member_level=user.get("member_level", info.member_level),
            is_use=(user.get("is_use", "Y") == "Y"),
            is_lock=(user.get("is_lock", "N") == "Y"),
        )
    
    # get_current_user_from_token이 성공한 경우
    return SessionValidateResponse(
        ok=True,
        user_id=user_info["user_id"],
        email=user_info["email"],
        display_name=user_info["display_name"],
        member_level=user_info.get("member_level", 1),
        is_use=(user_info.get("is_use", "Y") == "Y"),
        is_lock=(user_info.get("is_lock", "N") == "Y"),
    )
