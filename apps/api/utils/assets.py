# apps/api/utils/assets.py
"""
이미지 경로 정규화 유틸리티
R2 전체 URL 또는 절대 URL을 `/assets/...` 형식의 상대 경로로 변환
"""

from __future__ import annotations

from typing import Optional


def normalize_asset_path(url: Optional[str]) -> Optional[str]:
    """
    R2 전체 URL 또는 절대 URL을 받아서 `/assets/...` 이하의 상대 경로만 반환한다.
    이미 상대 경로(/assets/...)라면 그대로 반환한다.
    url 이 None 이면 None 반환.
    
    Args:
        url: 정규화할 이미지 URL
        
    Returns:
        정규화된 경로 또는 None
    """
    if not url:
        return url

    # 이미 /assets/ 로 시작하면 그대로 사용
    if url.startswith("/assets/"):
        return url

    # 전체 URL에 /assets/ 포함된 경우 → 그 뒤부터 사용
    idx = url.find("/assets/")
    if idx >= 0:
        return url[idx:]

    # http/https 이고 /assets/ 가 없으면 path 만 사용
    if url.startswith("http://") or url.startswith("https://"):
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.path or url
        except Exception:
            return url

    return url

