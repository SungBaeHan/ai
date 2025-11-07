# adapters/persistence/mongo/factory.py
"""
MongoDB Repository 팩토리
"""

from adapters.persistence.mongo.character_repository_adapter import MongoCharacterRepository
from src.ports.repositories.character_repository import CharacterRepository


def create_character_repository() -> CharacterRepository:
    """CharacterRepository 인스턴스 생성"""
    return MongoCharacterRepository()

