# adapters/persistence/mongo/__init__.py
"""
MongoDB 연결 및 초기화
"""

import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database

_client: Optional[MongoClient] = None
_db: Optional[Database] = None

def get_client() -> MongoClient:
    """MongoDB 클라이언트 싱글톤"""
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        _client = MongoClient(mongo_uri)
    return _client

def get_db() -> Database:
    """MongoDB 데이터베이스 싱글톤"""
    global _db
    if _db is None:
        db_name = os.getenv("MONGO_DB", "arcanaverse")
        _db = get_client()[db_name]
    return _db

def init_db() -> None:
    """인덱스 생성"""
    db = get_db()
    # characters 컬렉션 인덱스
    db.characters.create_index("id", unique=True)
    db.characters.create_index("image", unique=True)

