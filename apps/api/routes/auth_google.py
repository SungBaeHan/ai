# ========================================
# apps/api/routes/auth_google.py - Google OAuth 인증 API
# - POST /v1/auth/google: 구글 로그인 처리
# ========================================

import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests

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
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
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
            timeout=5
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        token_info = response.json()
        
        # 클라이언트 ID 확인 (옵션, 보안 강화)
        if GOOGLE_CLIENT_ID and token_info.get('aud') != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token audience mismatch")
        
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
    except HTTPException:
        raise
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


@router.post("/google")
async def google_login(request: GoogleLoginRequest):
    """
    구글 로그인 처리
    - Google Identity Services에서 받은 token 검증
    - JWT 토큰 생성 및 반환
    """
    try:
        # Google 토큰 검증
        user_info = verify_google_token(request.token)
        
        # JWT 토큰 생성
        access_token = create_jwt_token(user_info)
        
        # 응답 데이터
        return {
            'access_token': access_token,
            'email': user_info['email'],
            'name': user_info['name']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")








