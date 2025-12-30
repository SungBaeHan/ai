# apps/api/utils/auth_token.py
"""
인증 토큰 추출 유틸리티
"""

import logging
from fastapi import Request, HTTPException
from apps.api.utils.request_body import safe_json

logger = logging.getLogger(__name__)

BAD_TOKEN_VALUES = {"undefined", "null", "none", ""}


def _clean_token(raw: str | None) -> str | None:
    """토큰 후보를 정제합니다."""
    if not raw:
        return None
    t = raw.strip()
    if not t:
        return None
    if t.lower() in BAD_TOKEN_VALUES:
        return None
    # 너무 짧으면 대부분 쓰레기 값
    if len(t) < 20:
        return None
    return t


def _strip_bearer(v: str) -> str:
    """Bearer prefix를 제거합니다."""
    v = v.strip()
    if v.lower().startswith("bearer "):
        return v[7:].strip()
    return v


def _pfx(token: str, n: int = 12) -> str:
    """토큰의 앞 n자를 반환합니다."""
    return token[:n] if token else ""


async def extract_token(request: Request) -> str:
    """
    Request에서 인증 토큰을 추출합니다.
    여러 소스에서 토큰을 찾습니다 (우선순위 순).
    
    우선순위:
    1. Authorization: Bearer <token> 헤더
    2. Authorization: <token> (Bearer 없이)
    3. X-Authorization: Bearer <token>
    4. X-Access-Token: <token>
    5. Cookie: access_token / token / session
    6. JSON body의 token 필드
    
    Args:
        request: FastAPI Request 객체
    
    Returns:
        추출된 토큰 문자열
    
    Raises:
        HTTPException(401): 토큰을 찾을 수 없거나 유효하지 않은 경우
    """
    # 디버그용: 각 소스 존재 여부 체크
    auth_header_exists = "Authorization" in request.headers
    x_auth_header_exists = "X-Authorization" in request.headers
    x_access_token_exists = "X-Access-Token" in request.headers
    x_user_info_token_exists = "X-User-Info-Token" in request.headers
    cookie_access_token_exists = "access_token" in request.cookies
    cookie_token_exists = "token" in request.cookies
    cookie_session_exists = "session" in request.cookies
    
    # JSON body 체크는 safe_json 호출 시 수행
    body_token_exists = False
    
    logger.info(
        "[AUTH][TOKEN_SRC] auth_header=%s x_auth=%s x_access=%s x_user_info=%s cookie_access=%s cookie_token=%s cookie_session=%s body_token=%s",
        auth_header_exists,
        x_auth_header_exists,
        x_access_token_exists,
        x_user_info_token_exists,
        cookie_access_token_exists,
        cookie_token_exists,
        cookie_session_exists,
        body_token_exists,
    )
    
    # 1) Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header:
        candidate = _clean_token(_strip_bearer(auth_header))
        if candidate:
            logger.info(
                "[AUTH][TRACE] token_source=authorization_bearer len=%s prefix=%s",
                len(candidate),
                _pfx(candidate),
            )
            return candidate
        # Bearer 없이 Authorization 헤더에 직접 토큰이 있는 경우
        candidate = _clean_token(auth_header)
        if candidate:
            logger.info(
                "[AUTH][TRACE] token_source=authorization_direct len=%s prefix=%s",
                len(candidate),
                _pfx(candidate),
            )
            return candidate
    
    # 2) X-Authorization: Bearer <token>
    x_auth_header = request.headers.get("X-Authorization")
    if x_auth_header:
        candidate = _clean_token(_strip_bearer(x_auth_header))
        if candidate:
            logger.info(
                "[AUTH][TRACE] token_source=x_authorization len=%s prefix=%s",
                len(candidate),
                _pfx(candidate),
            )
            return candidate
    
    # 3) X-Access-Token: <token>
    x_access_token = request.headers.get("X-Access-Token")
    if x_access_token:
        candidate = _clean_token(x_access_token)
        if candidate:
            logger.info(
                "[AUTH][TRACE] token_source=x_access_token len=%s prefix=%s",
                len(candidate),
                _pfx(candidate),
            )
            return candidate
    
    # 3-1) X-User-Info-Token: <token> (하위 호환)
    x_user_info_token = request.headers.get("X-User-Info-Token")
    if x_user_info_token:
        candidate = _clean_token(x_user_info_token)
        if candidate:
            logger.info(
                "[AUTH][TRACE] token_source=x_user_info_token len=%s prefix=%s",
                len(candidate),
                _pfx(candidate),
            )
            return candidate
    
    # 4) Cookie: access_token / token / session
    cookie_token = request.cookies.get("access_token") or request.cookies.get("token") or request.cookies.get("session")
    if cookie_token:
        candidate = _clean_token(cookie_token)
        if candidate:
            cookie_source = "cookie_access_token" if request.cookies.get("access_token") else ("cookie_token" if request.cookies.get("token") else "cookie_session")
            logger.info(
                "[AUTH][TRACE] token_source=%s len=%s prefix=%s",
                cookie_source,
                len(candidate),
                _pfx(candidate),
            )
            return candidate
    
    # 5) JSON body의 token 필드 (최후순위)
    try:
        body = await safe_json(request)
        body_token = body.get("token")
        if body_token:
            candidate = _clean_token(str(body_token))
            if candidate:
                logger.info(
                    "[AUTH][TRACE] token_source=body len=%s prefix=%s",
                    len(candidate),
                    _pfx(candidate),
                )
                return candidate
    except HTTPException:
        raise
    except Exception as e:
        # body 파싱 실패는 무시 (다른 소스에서 찾을 수 있음)
        logger.debug("[AUTH][TRACE] body parsing failed (ignored): %s", str(e))
    
    # 토큰을 찾지 못함
    logger.warning("[AUTH][TOKEN] source=none - token not found in any source")
    raise HTTPException(status_code=401, detail="Missing token")

