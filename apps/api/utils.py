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


def build_r2_public_url(key_or_path: Optional[str]) -> Optional[str]:
    """
    R2 public URL을 생성합니다.
    
    Args:
        key_or_path: R2 object key 또는 경로 (예: "char/lily_01.png" 또는 "/assets/char/lily_01.png")
    
    Returns:
        R2 public URL (예: "https://pub-09b0f3cad63f4891868948d43f19febf.r2.dev/char/lily_01.png")
        key_or_path가 None이거나 빈 문자열이면 None 반환
        R2_PUBLIC_BASE_URL이 설정되지 않았으면 None 반환
    """
    if not key_or_path:
        return None
    
    # 이미 전체 URL인 경우 그대로 반환
    if key_or_path.startswith("http://") or key_or_path.startswith("https://"):
        return key_or_path
    
    # R2 public base URL 가져오기
    r2_base = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")
    if not r2_base:
        return None
    
    # 경로 정규화: /assets/char/xxx.png -> char/xxx.png
    # 또는 /char/xxx.png -> char/xxx.png
    key = key_or_path.lstrip("/")
    if key.startswith("assets/"):
        key = key[7:]  # "assets/" 제거
    
    # R2 URL 생성
    return f"{r2_base}/{key}"


