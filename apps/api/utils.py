# apps/api/utils.py
"""
공통 유틸리티 함수
"""
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


