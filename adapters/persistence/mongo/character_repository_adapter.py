# adapters/persistence/mongo/character_repository_adapter.py
"""
MongoDB CharacterRepository 어댑터
"""

from typing import List, Optional
from src.domain.character import Character
from src.ports.repositories.character_repository import CharacterRepository


class MongoCharacterRepository(CharacterRepository):
    """MongoDB 구현체"""
    
    def __init__(self):
        import os
        # 환경변수 우선순위: MONGODB_URI > MONGO_URI (하위 호환성)
        # MONGO_DB_NAME > MONGO_DB (하위 호환성)
        # MONGO_URI: mongodb+srv://user:password@host/db 형식 필요
        # DB명이 URI에 없으면 기본값 /arcanaverse 사용
        # 예: mongodb+srv://user:pass@cluster.mongodb.net/arcanaverse?retryWrites=true&w=majority
        self._uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        self._db_name = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB", "arcanaverse")
        self._client = None
        self._db = None
        self.collection = None
    
    def _ensure(self):
        from pymongo import MongoClient
        import certifi, re
        if not self._client:
            if not self._uri:
                raise RuntimeError("MONGO_URI is not set.")
            # require SRV uri to avoid host/replicaset/cipher mismatches
            if not self._uri.startswith("mongodb+srv://"):
                raise RuntimeError(
                    f"MONGO_URI must use 'mongodb+srv://'. Got: {self._uri.split('@')[0]}@[redacted]"
                )
            self._client = MongoClient(
                self._uri,
                appname="arcanaverse-api",
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
            )
            self._db = self._client[self._db_name]
            self.collection = self._db["characters"]
    
    def get_by_id(self, char_id: int) -> Optional[Character]:
        """ID로 캐릭터 조회"""
        self._ensure()
        doc = self.collection.find_one({"id": char_id})
        if not doc:
            return None
        # _id 제거
        doc.pop("_id", None)
        return Character.from_dict(doc)
    
    def list_all(self, offset: int = 0, limit: int = 30) -> List[Character]:
        """캐릭터 목록 조회"""
        self._ensure()
        cursor = self.collection.find().sort("id", 1).skip(offset).limit(limit)
        items = []
        for doc in cursor:
            doc.pop("_id", None)
            items.append(Character.from_dict(doc))
        return items
    
    def count(self) -> int:
        """캐릭터 총 개수 조회"""
        self._ensure()
        return self.collection.count_documents({})
    
    def create(self, character: Character) -> Character:
        """새 캐릭터 생성"""
        self._ensure()
        data = character.to_dict()
        self.collection.insert_one(data)
        return character
    
    def upsert_by_image(self, character: Character) -> Character:
        """이미지 경로로 캐릭터 upsert"""
        self._ensure()
        data = character.to_dict()
        self.collection.update_one(
            {"image": character.image},
            {"$set": data},
            upsert=True
        )
        return character
    
    def list_paginated(self, skip: int = 0, limit: int = 20, q: str = None):
        self._ensure()
        query = {}
        if q:
            # 텍스트 인덱스가 없다면 간단한 부분일치로 대체
            query = {"$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
                {"summary": {"$regex": q, "$options": "i"}},
            ]}
        cur = self.collection.find(query, {"_id": 0}).skip(max(0,skip)).limit(max(1,min(limit,100)))
        items = list(cur)
        total = self.collection.count_documents(query)
        return {"total": int(total), "items": items}

