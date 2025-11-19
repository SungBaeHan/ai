# apps/api/utils.py
"""
공통 유틸리티 함수
"""
import os
import re
from typing import Optional


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


def build_public_image_url(src_file: Optional[str]) -> Optional[str]:
    """
    R2 public image URL을 생성합니다.
    
    Args:
        src_file: 소스 파일명 (예: "lily_01.png", "char/lily_01.png", "/assets/char/lily_01.png")
                  기존 접두사는 무시되고 파일명만 추출됩니다.
    
    Returns:
        R2 public URL (예: "https://pub-09b0f3cad63f4891868948d43f19febf.r2.dev/assets/char/lily_01.png")
        src_file이 None이거나 빈 문자열이면 None 반환
        R2_PUBLIC_BASE_URL이 설정되지 않았으면 None 반환
        이미 전체 URL인 경우 그대로 반환
    """
    if not src_file:
        return None
    
    # 이미 전체 URL인 경우 그대로 반환
    if src_file.startswith("http://") or src_file.startswith("https://"):
        return src_file
    
    # R2 public base URL 가져오기
    r2_base = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")
    if not r2_base:
        return None
    
    # 파일명 추출: 기존 접두사 제거
    # "/assets/char/lily_01.png" -> "lily_01.png"
    # "char/lily_01.png" -> "lily_01.png"
    # "lily_01.png" -> "lily_01.png"
    filename = src_file.lstrip("/")
    if "/" in filename:
        # 마지막 경로 세그먼트만 추출 (파일명)
        filename = filename.split("/")[-1]
    
    # R2 URL 생성: 항상 /assets/char/ 접두사 사용
    return f"{r2_base}/assets/char/{filename}"


# 하위 호환성을 위한 별칭
def build_r2_public_url(key_or_path: Optional[str]) -> Optional[str]:
    """Deprecated: build_public_image_url()를 사용하세요."""
    return build_public_image_url(key_or_path)


