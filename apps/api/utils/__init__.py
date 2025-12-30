# apps/api/utils/__init__.py
"""
API 유틸리티 패키지
"""

# 주요 공통 유틸리티 함수 re-export
from .common import (
    mask_mongo_uri,
    build_public_image_url,
    build_public_image_url_from_path,
)

# 하위 호환을 위한 deprecated 함수도 export (사용 빈도는 낮지만 기존 코드 호환)
from .common import build_r2_public_url  # Deprecated

__all__ = [
    "mask_mongo_uri",
    "build_public_image_url",
    "build_public_image_url_from_path",
    "build_r2_public_url",  # Deprecated
]

