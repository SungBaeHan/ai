# adapters/persistence/mongo/character_repository_adapter.py
"""
MongoDB CharacterRepository 어댑터
"""

from typing import List, Optional
from src.domain.character import Character
from src.ports.repositories.character_repository import CharacterRepository
from adapters.persistence.mongo import get_db


class MongoCharacterRepository(CharacterRepository):
    """MongoDB 구현체"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.characters
    
    def get_by_id(self, char_id: int) -> Optional[Character]:
        """ID로 캐릭터 조회"""
        doc = self.collection.find_one({"id": char_id})
        if not doc:
            return None
        # _id 제거
        doc.pop("_id", None)
        return Character.from_dict(doc)
    
    def list_all(self, offset: int = 0, limit: int = 30) -> List[Character]:
        """캐릭터 목록 조회"""
        cursor = self.collection.find().sort("id", 1).skip(offset).limit(limit)
        items = []
        for doc in cursor:
            doc.pop("_id", None)
            items.append(Character.from_dict(doc))
        return items
    
    def count(self) -> int:
        """캐릭터 총 개수 조회"""
        return self.collection.count_documents({})
    
    def create(self, character: Character) -> Character:
        """새 캐릭터 생성"""
        data = character.to_dict()
        self.collection.insert_one(data)
        return character
    
    def upsert_by_image(self, character: Character) -> Character:
        """이미지 경로로 캐릭터 upsert"""
        data = character.to_dict()
        self.collection.update_one(
            {"image": character.image},
            {"$set": data},
            upsert=True
        )
        return character

