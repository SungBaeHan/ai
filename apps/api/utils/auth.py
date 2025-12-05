# apps/api/utils/auth.py
"""
인증 유틸리티 함수
"""

from typing import Optional
from fastapi import Request, Depends
from pydantic import BaseModel

try:
    import jwt
except ImportError:
    try:
        import PyJWT as jwt
    except ImportError:
        jwt = None

import os

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"


class User(BaseModel):
    """사용자 모델"""
    sub: str
    email: str
    name: Optional[str] = None


def decode_jwt_token(token: str) -> Optional[dict]:
    """JWT 토큰 디코드"""
    if not jwt:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


def get_optional_user(request: Request) -> Optional[User]:
    """
    선택적 사용자 인증.
    Authorization 헤더가 있으면 사용자 정보를 반환하고, 없으면 None을 반환합니다.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    
    if not payload:
        return None
    
    return User(
        sub=payload.get("sub", ""),
        email=payload.get("email", ""),
        name=payload.get("name"),
    )

