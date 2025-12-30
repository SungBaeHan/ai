# apps/api/deps/auth.py
"""
인증 의존성 함수
"""

import logging
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from bson import ObjectId

from apps.api.utils.auth_token import extract_token
from apps.api.core.user_info_token import decode_user_info_token
from adapters.persistence.mongo.factory import get_mongo_client

logger = logging.getLogger(__name__)


async def get_current_user_from_token(request: Request) -> dict:
    """
    Request에서 토큰을 추출하고 검증하여 사용자 정보를 반환합니다.
    validate-session과 완전히 동일한 로직을 사용합니다.
    
    Args:
        request: FastAPI Request 객체
    
    Returns:
        사용자 정보 딕셔너리:
        {
            "user_id": str,
            "email": str,
            "display_name": str,
            "google_id": str,
            "sub": str,
            "is_use": str,
            "is_lock": str,
        }
    
    Raises:
        HTTPException(401): 토큰이 없거나 유효하지 않은 경우
    """
    # 토큰 추출 (extract_token 사용)
    try:
        token = await extract_token(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[AUTH][ERROR] Failed to extract token: %s", str(e))
        raise HTTPException(status_code=401, detail="Failed to extract token")
    
    # 토큰 디코드
    try:
        info = decode_user_info_token(token)
    except ValueError as e:
        logger.warning("[AUTH][ERROR] Token decode failed: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid or malformed token")
    except Exception as e:
        logger.exception("[AUTH][ERROR] Token decode error: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid or malformed token")

    # 토큰 만료 확인
    now = datetime.now(timezone.utc)
    if info.expired_at < now:
        logger.warning("[AUTH][ERROR] Token expired: expired_at=%s, now=%s", info.expired_at, now)
        raise HTTPException(status_code=401, detail="Token expired")

    # 사용자 조회
    db = get_mongo_client()
    users = db.users

    try:
        user = users.find_one({"_id": ObjectId(info.user_id)})
    except Exception as e:
        logger.warning("[AUTH][ERROR] Invalid user_id in token: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    if not user:
        logger.warning("[AUTH][ERROR] User not found: user_id=%s", info.user_id)
        raise HTTPException(status_code=401, detail="User not found")

    # last_login_at 검증 (세션 토큰 무효화 체크)
    db_last_login = user.get("last_login_at")
    if db_last_login is None:
        logger.warning("[AUTH][ERROR] User session invalid: no last_login_at for user_id=%s", info.user_id)
        raise HTTPException(status_code=401, detail="User session invalid (no last_login_at)")

    # timezone 정보가 없으면 UTC로 가정
    if isinstance(db_last_login, datetime):
        if db_last_login.tzinfo is None:
            db_last_login = db_last_login.replace(tzinfo=timezone.utc)
    else:
        logger.warning("[AUTH][ERROR] Invalid last_login_at format: %s", type(db_last_login))
        raise HTTPException(status_code=401, detail="Invalid last_login_at format")

    # last_login_at 비교 (마이크로초 단위 차이 무시)
    if db_last_login.replace(microsecond=0) != info.last_login_at.replace(microsecond=0):
        logger.warning(
            "[AUTH][ERROR] User session invalid: last_login_at mismatch. db=%s, token=%s",
            db_last_login,
            info.last_login_at,
        )
        raise HTTPException(status_code=401, detail="User session invalid (last_login_at mismatch)")

    # 사용자 정보 반환 (dict 형태, validate-session과 동일한 구조)
    return {
        "user_id": str(user["_id"]),
        "email": user.get("email", info.email),
        "display_name": user.get("display_name", info.display_name),
        "google_id": user.get("google_id"),
        "sub": user.get("google_id"),
        "member_level": user.get("member_level", info.member_level),
        "is_use": user.get("is_use", "Y"),
        "is_lock": user.get("is_lock", "N"),
    }
