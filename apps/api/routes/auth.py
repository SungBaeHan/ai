# ========================================
# apps/api/routes/auth.py - 인증 API
# - GET /v1/auth/me: 현재 사용자 정보
# - POST /v1/auth/logout: 로그아웃 (토큰 무효화)
# 주의: /v1/auth/google은 auth_google.py에서 처리합니다.
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


@router.get("/me")
async def get_current_user(req: Request):
    """
    현재 로그인한 사용자 정보 조회
    """
    # Authorization 헤더에서 토큰 추출
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        'sub': payload.get('sub'),
        'email': payload.get('email'),
        'name': payload.get('name')
    }


@router.post("/logout")
async def logout():
    """
    로그아웃 (클라이언트에서 토큰 삭제 처리, 서버에서는 토큰 무효화 목록 관리 가능)
    """
    # 실제로는 토큰 무효화 목록(블랙리스트)에 추가하거나,
    # 짧은 만료 시간으로 인해 클라이언트에서만 삭제해도 됨
    return {"message": "Logged out successfully"}
