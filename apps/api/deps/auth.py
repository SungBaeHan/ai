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


def _looks_like_jwt(token: str) -> bool:
    """JWT 토큰인지 확인 (header.payload.signature 형태)"""
    return token.count(".") == 2


def _prefix(token: str, n: int = 12) -> str:
    """토큰의 앞 n자를 반환합니다."""
    try:
        return token[:n]
    except Exception:
        return "<?>"


async def _decode_jwt_access_token(token: str, request: Request) -> dict | None:
    """
    JWT 토큰을 검증하고 사용자 정보를 반환합니다.
    validate-session에서 사용하는 JWT 검증 로직과 동일하게 맞춘다.
    """
    from apps.api.routes.auth import decode_jwt_token
    from adapters.persistence.mongo.factory import get_mongo_client
    
    # JWT 디코드
    try:
        payload = decode_jwt_token(token)
    except Exception as e:
        logger.warning("[AUTH][TRACE] jwt_decode_failed path=%s err=%s", getattr(request.url, "path", "<?>"), str(e))
        return None
    
    if not payload:
        logger.warning("[AUTH][TRACE] jwt_decode_returned_none path=%s", getattr(request.url, "path", "<?>"))
        return None
    
    # JWT의 sub (Google user ID)로 MongoDB에서 user 조회
    db = get_mongo_client()
    users = db.users
    
    google_id = payload.get('sub')
    if not google_id:
        logger.warning("[AUTH][TRACE] jwt_no_sub_in_payload path=%s", getattr(request.url, "path", "<?>"))
        return None
    
    # google_id 또는 email로 user 조회
    user = users.find_one({
        "$or": [
            {"google_id": google_id},
            {"email": payload.get('email')}
        ]
    })
    
    if not user:
        logger.warning("[AUTH][TRACE] jwt_user_not_found path=%s google_id=%s", getattr(request.url, "path", "<?>"), google_id)
        return None
    
    # 사용자 정보 반환 (validate-session과 동일한 구조)
    return {
        'user_id': str(user['_id']),  # MongoDB ObjectId를 문자열로 변환
        'sub': google_id,
        'email': user.get('email', payload.get('email')),
        'display_name': user.get('display_name', payload.get('name')),
        'google_id': user.get('google_id', google_id),
        'member_level': user.get('member_level', 1),
        'is_use': 'Y' if user.get('is_use', 'Y') == 'Y' else 'N',
        'is_lock': 'Y' if user.get('is_lock', 'N') == 'Y' else 'N',
    }


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
        logger.exception("[AUTH][TRACE][ERROR] extract_token_failed path=%s err=%s", getattr(request.url, "path", "<?>"), str(e))
        raise HTTPException(status_code=401, detail="Failed to extract token")
    
    if not token:
        logger.warning("[AUTH][TRACE] no_token path=%s", getattr(request.url, "path", "<?>"))
        raise HTTPException(status_code=401, detail="Missing token")

    # ✅ 여기서 어떤 토큰이 들어왔는지 찍기
    is_jwt = _looks_like_jwt(token)
    logger.info(
        "[AUTH][TRACE] token_received path=%s is_jwt=%s len=%s prefix=%s",
        getattr(request.url, "path", "<?>"),
        is_jwt,
        len(token),
        _prefix(token),
    )

    # JWT 또는 user_info_v2 토큰 검증
    try:
        if is_jwt:
            logger.info(
                "[AUTH][TRACE] jwt_token_detected_and_supported path=%s prefix=%s",
                getattr(request.url, "path", "<?>"),
                _prefix(token),
            )
            user = await _decode_jwt_access_token(token, request)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid JWT token")
            logger.info("[AUTH][TRACE] jwt_decode_ok path=%s user_id=%s", getattr(request.url, "path", "<?>"), user.get("user_id", "<?>"))
            return user
        else:
            # user_info_v2 토큰 검증
            logger.info("[AUTH][TRACE] using_user_info_v2_decoder path=%s", getattr(request.url, "path", "<?>"))
            info = decode_user_info_token(token)
            logger.info("[AUTH][TRACE] user_info_v2_decode_ok path=%s user_id=%s", getattr(request.url, "path", "<?>"), getattr(info, "user_id", None))
    except HTTPException:
        raise
    except ValueError as e:
        logger.exception(
            "[AUTH][TRACE][ERROR] decode_failed path=%s is_jwt=%s prefix=%s err=%s",
            getattr(request.url, "path", "<?>"),
            is_jwt,
            _prefix(token),
            str(e),
        )
        raise HTTPException(status_code=401, detail="Invalid or malformed token")
    except Exception as e:
        logger.exception(
            "[AUTH][TRACE][ERROR] decode_error path=%s is_jwt=%s prefix=%s err=%s",
            getattr(request.url, "path", "<?>"),
            is_jwt,
            _prefix(token),
            str(e),
        )
        raise HTTPException(status_code=401, detail="Invalid or malformed token")

    # 토큰 만료 확인
    now = datetime.now(timezone.utc)
    if info.expired_at < now:
        logger.warning("[AUTH][TRACE][ERROR] token_expired path=%s expired_at=%s now=%s", getattr(request.url, "path", "<?>"), info.expired_at, now)
        raise HTTPException(status_code=401, detail="Token expired")

    # 사용자 조회
    db = get_mongo_client()
    users = db.users

    try:
        user = users.find_one({"_id": ObjectId(info.user_id)})
    except Exception as e:
        logger.warning("[AUTH][TRACE][ERROR] invalid_user_id path=%s user_id=%s err=%s", getattr(request.url, "path", "<?>"), getattr(info, "user_id", None), str(e))
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    if not user:
        logger.warning(
            "[AUTH][TRACE][ERROR] user_none_after_decode path=%s user_id=%s",
            getattr(request.url, "path", "<?>"),
            getattr(info, "user_id", None),
        )
        raise HTTPException(status_code=401, detail="User not found")

    # last_login_at 검증 (세션 토큰 무효화 체크)
    db_last_login = user.get("last_login_at")
    if db_last_login is None:
        logger.warning("[AUTH][TRACE][ERROR] no_last_login_at path=%s user_id=%s", getattr(request.url, "path", "<?>"), str(user.get("_id", "<?>")))
        raise HTTPException(status_code=401, detail="User session invalid (no last_login_at)")

    # timezone 정보가 없으면 UTC로 가정
    if isinstance(db_last_login, datetime):
        if db_last_login.tzinfo is None:
            db_last_login = db_last_login.replace(tzinfo=timezone.utc)
    else:
        logger.warning("[AUTH][TRACE][ERROR] invalid_last_login_at_format path=%s user_id=%s type=%s", getattr(request.url, "path", "<?>"), str(user.get("_id", "<?>")), type(db_last_login))
        raise HTTPException(status_code=401, detail="Invalid last_login_at format")

    # last_login_at 비교 (마이크로초 단위 차이 무시)
    if db_last_login.replace(microsecond=0) != info.last_login_at.replace(microsecond=0):
        logger.warning(
            "[AUTH][TRACE][ERROR] last_login_at_mismatch path=%s user_id=%s db=%s token=%s",
            getattr(request.url, "path", "<?>"),
            str(user.get("_id", "<?>")),
            db_last_login,
            info.last_login_at,
        )
        raise HTTPException(status_code=401, detail="User session invalid (last_login_at mismatch)")

    # 사용자 정보 반환 (dict 형태, validate-session과 동일한 구조)
    logger.info("[AUTH][TRACE] auth_success path=%s user_id=%s", getattr(request.url, "path", "<?>"), str(user.get("_id", "<?>")))
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


# Public alias for consistency
# 모든 router는 이 함수를 사용해야 합니다.
get_current_user = get_current_user_from_token
