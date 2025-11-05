# src/usecases/character/list_characters.py
"""
캐릭터 목록 조회 유즈케이스
"""

from typing import List
from src.domain.character import Character
from src.ports.repositories.character_repository import CharacterRepository


class ListCharactersUseCase:
    """캐릭터 목록 조회 유즈케이스"""
    
    def __init__(self, repository: CharacterRepository):
        self.repository = repository
    
    def execute(self, offset: int = 0, limit: int = 30) -> List[Character]:
        """캐릭터 목록 조회 실행"""
        return self.repository.list_all(offset=offset, limit=limit)
