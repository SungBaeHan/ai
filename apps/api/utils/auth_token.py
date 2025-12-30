# apps/api/utils/auth_token.py
"""
인증 토큰 추출 유틸리티
"""

import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


def extract_token(request: Request) -> str:
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
    cookie_access_token_exists = "access_token" in request.cookies
    cookie_token_exists = "token" in request.cookies
    cookie_session_exists = "session" in request.cookies
    
    # JSON body 체크는 나중에 필요시 수행
    body_token_exists = False
    
    logger.info(
        "[AUTH][TOKEN_SRC] auth_header=%s x_auth=%s x_access=%s cookie_access=%s cookie_token=%s cookie_session=%s body_token=%s",
        auth_header_exists,
        x_auth_header_exists,
        x_access_token_exists,
        cookie_access_token_exists,
        cookie_token_exists,
        cookie_session_exists,
        body_token_exists,
    )
    
    # 1) Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                logger.info(
                    "[AUTH][TOKEN] source=authorization_bearer len=%d prefix=%s",
                    len(token),
                    token[:8] if len(token) >= 8 else token,
                )
                if len(token) < 20:
                    raise HTTPException(status_code=401, detail="Invalid or malformed token")
                return token
        else:
            # Bearer 없이 Authorization 헤더에 직접 토큰이 있는 경우
            token = auth_header.strip()
            if token:
                logger.info(
                    "[AUTH][TOKEN] source=authorization_direct len=%d prefix=%s",
                    len(token),
                    token[:8] if len(token) >= 8 else token,
                )
                if len(token) < 20:
                    raise HTTPException(status_code=401, detail="Invalid or malformed token")
                return token
    
    # 2) X-Authorization: Bearer <token>
    x_auth_header = request.headers.get("X-Authorization")
    if x_auth_header:
        if x_auth_header.startswith("Bearer "):
            token = x_auth_header[7:].strip()
        else:
            token = x_auth_header.strip()
        if token:
            logger.info(
                "[AUTH][TOKEN] source=x_authorization len=%d prefix=%s",
                len(token),
                token[:8] if len(token) >= 8 else token,
            )
            if len(token) < 20:
                raise HTTPException(status_code=401, detail="Invalid or malformed token")
            return token
    
    # 3) X-Access-Token: <token>
    x_access_token = request.headers.get("X-Access-Token")
    if x_access_token:
        token = x_access_token.strip()
        if token:
            logger.info(
                "[AUTH][TOKEN] source=x_access_token len=%d prefix=%s",
                len(token),
                token[:8] if len(token) >= 8 else token,
            )
            if len(token) < 20:
                raise HTTPException(status_code=401, detail="Invalid or malformed token")
            return token
    
    # 3-1) X-User-Info-Token: <token> (하위 호환)
    x_user_info_token = request.headers.get("X-User-Info-Token")
    if x_user_info_token:
        token = x_user_info_token.strip()
        if token:
            logger.info(
                "[AUTH][TOKEN] source=x_user_info_token len=%d prefix=%s",
                len(token),
                token[:8] if len(token) >= 8 else token,
            )
            if len(token) < 20:
                raise HTTPException(status_code=401, detail="Invalid or malformed token")
            return token
    
    # 4) Cookie: access_token / token / session
    cookie_token = request.cookies.get("access_token") or request.cookies.get("token") or request.cookies.get("session")
    if cookie_token:
        token = cookie_token.strip()
        if token:
            logger.info(
                "[AUTH][TOKEN] source=cookie len=%d prefix=%s",
                len(token),
                token[:8] if len(token) >= 8 else token,
            )
            if len(token) < 20:
                raise HTTPException(status_code=401, detail="Invalid or malformed token")
            return token
    
    # 5) JSON body의 token 필드는 호출하는 쪽에서 body를 파싱한 후 전달해야 함
    # extract_token_from_body() 같은 별도 함수로 처리하거나,
    # validate-session처럼 body에서 직접 받는 경우는 별도 처리
    
    # 토큰을 찾지 못함
    logger.warning("[AUTH][TOKEN] source=none - token not found in any source")
    raise HTTPException(status_code=401, detail="Missing token")

