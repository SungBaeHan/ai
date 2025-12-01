# adapters/persistence/mongo/factory.py
"""
MongoDB Repository 팩토리
"""

from adapters.persistence.mongo.character_repository_adapter import MongoCharacterRepository
from src.ports.repositories.character_repository import CharacterRepository
from adapters.persistence.mongo import get_db


def create_character_repository() -> CharacterRepository:
    """CharacterRepository 인스턴스 생성"""
    return MongoCharacterRepository()


def get_mongo_client():
    """MongoDB 데이터베이스 인스턴스 반환 (user.py에서 사용)"""
    return get_db()

