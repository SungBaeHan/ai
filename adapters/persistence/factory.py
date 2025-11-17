# adapters/persistence/factory.py
"""
Repository 팩토리 - 환경변수에 따라 적절한 Repository 반환
"""

import os
from src.ports.repositories.character_repository import CharacterRepository

def get_character_repo() -> CharacterRepository:
    """환경변수에 따라 적절한 CharacterRepository 반환"""
    # DB_BACKEND 우선, 없으면 DATA_BACKEND (하위 호환성), 기본값은 mongo
    backend = os.getenv("DB_BACKEND") or os.getenv("DATA_BACKEND", "mongo")
    backend = backend.lower()
    
    if backend == "mongo":
        from adapters.persistence.mongo.factory import create_character_repository
        return create_character_repository()
    elif backend == "sqlite":
        # SQLite 사용 시에만 초기화
        from adapters.persistence.sqlite.character_repository_adapter import SQLiteCharacterRepository
        return SQLiteCharacterRepository()
    else:
        raise RuntimeError(f"Unsupported DB_BACKEND: {backend}. Supported values: 'mongo', 'sqlite'")

