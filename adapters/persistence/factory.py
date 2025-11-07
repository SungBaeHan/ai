# adapters/persistence/factory.py
"""
Repository 팩토리 - 환경변수에 따라 적절한 Repository 반환
"""

import os
from src.ports.repositories.character_repository import CharacterRepository

def get_character_repo() -> CharacterRepository:
    """환경변수에 따라 적절한 CharacterRepository 반환"""
    backend = os.getenv("DATA_BACKEND", "mongo").lower()
    
    if backend == "mongo":
        from adapters.persistence.mongo.factory import create_character_repository
        return create_character_repository()
    else:
        # SQLite fallback
        from adapters.persistence.sqlite.character_repository_adapter import SQLiteCharacterRepository
        return SQLiteCharacterRepository()

