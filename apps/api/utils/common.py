# apps/api/utils/common.py
"""
공통 유틸리티 함수
"""
import os
import re
from typing import Optional
from urllib.parse import urlparse

from apps.api.config import settings


def mask_mongo_uri(uri: Optional[str]) -> str:
    """
    MongoDB URI의 비밀번호 부분을 마스킹하여 반환.
    
    예: mongodb+srv://user:password@host/db
        -> mongodb+srv://user:*****@host/db
    
    Args:
        uri: 마스킹할 MongoDB URI (None 가능)
    
    Returns:
        마스킹된 URI 문자열. None이면 빈 문자열 반환.
    """
    if not uri:
        return ""
    # mongodb+srv://user:password@host 패턴을 mongodb+srv://user:*****@host로 변경
    return re.sub(r'(mongodb\+srv://[^:]+):[^@]+@', r'\1:*****@', uri)


def build_public_image_url(src_file: Optional[str], prefix: str = "char") -> Optional[str]:
    """
    R2 public image URL을 생성합니다.
    
    Args:
        src_file: 소스 파일명 (예: "lily_01.png", "char/lily_01.png", "/assets/char/lily_01.png")
                  기존 접두사는 무시되고 파일명만 추출됩니다.
        prefix: 이미지 타입 접두사 ("char" 또는 "world", 기본값: "char")
    
    Returns:
        Asset public URL (예: "https://img.arcanaverse.ai/assets/char/lily_01.png")
        src_file이 None이거나 빈 문자열이면 None 반환
        ASSET_BASE_URL이 설정되지 않았으면 None 반환
        이미 전체 URL인 경우 그대로 반환
    """
    if not src_file:
        return None
    
    # 이미 전체 URL인 경우: r2.dev 등 비-CDN 도메인이면 CDN으로 정규화 (API 응답에서 R2 도메인 미노출)
    if src_file.startswith("http://") or src_file.startswith("https://"):
        if "r2.dev" in src_file:
            # path 추출 (예: https://pub-xxx.r2.dev/assets/char/x.png → /assets/char/x.png)
            try:
                parsed = urlparse(src_file)
                path = parsed.path or ""
                if path.startswith("/"):
                    asset_base = settings.ASSET_BASE_URL
                    if asset_base:
                        return f"{asset_base.rstrip('/')}{path}"
                return src_file
            except Exception:
                return src_file
        return src_file
    
    # Asset base URL (CDN 기본값)
    asset_base = settings.ASSET_BASE_URL
    if not asset_base:
        return None
    
    # 파일명 추출: 기존 접두사 제거
    # "/assets/char/lily_01.png" -> "lily_01.png"
    # "char/lily_01.png" -> "lily_01.png"
    # "lily_01.png" -> "lily_01.png"
    filename = src_file.lstrip("/")
    if "/" in filename:
        # 마지막 경로 세그먼트만 추출 (파일명)
        filename = filename.split("/")[-1]
    
    # Asset URL 생성: prefix에 따라 /assets/char/ 또는 /assets/world/ 접두사 사용
    return f"{asset_base}/assets/{prefix}/{filename}"


def build_public_image_url_from_path(path: Optional[str]) -> Optional[str]:
    """
    /assets/... 형식의 경로를 R2 public URL로 변환합니다.
    경로에서 prefix를 자동으로 추출합니다.
    
    Args:
        path: 이미지 경로 (예: "/assets/game/xxx.png", "/assets/world/xxx.png", "/assets/char/xxx.png")
    
    Returns:
        R2 public URL 또는 None
    """
    if not path:
        return None
    
    # 이미 전체 URL인 경우: r2.dev 이면 CDN으로 정규화 (build_public_image_url과 동일)
    if path.startswith("http://") or path.startswith("https://"):
        return build_public_image_url(path)

    # /assets/로 시작하지 않으면 build_public_image_url 사용 (기존 로직)
    if not path.startswith("/assets/"):
        return build_public_image_url(path)
    
    # Asset base URL (CDN 기본값)
    asset_base = settings.ASSET_BASE_URL
    if not asset_base:
        return None
    
    # /assets/xxx/... 형식이면 그대로 사용
    return f"{asset_base}{path}"


# 하위 호환성을 위한 별칭
def build_r2_public_url(key_or_path: Optional[str]) -> Optional[str]:
    """Deprecated: build_public_image_url()를 사용하세요."""
    return build_public_image_url(key_or_path)

