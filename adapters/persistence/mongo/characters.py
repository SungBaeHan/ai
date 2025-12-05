# adapters/persistence/mongo/characters.py
"""
MongoDB characters 컬렉션 직접 접근 유틸리티
"""

from adapters.persistence.mongo import get_db

def get_characters_collection():
    """characters 컬렉션 반환"""
    db = get_db()
    return db["characters"]

# 편의를 위한 전역 변수 (lazy initialization)
_characters_collection = None

def characters_collection():
    """characters 컬렉션 싱글톤"""
    global _characters_collection
    if _characters_collection is None:
        _characters_collection = get_characters_collection()
    return _characters_collection

