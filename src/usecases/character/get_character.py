# src/usecases/character/get_character.py
"""
캐릭터 조회 유즈케이스
"""

from typing import Optional
from src.domain.character import Character
from src.ports.repositories.character_repository import CharacterRepository


class GetCharacterUseCase:
    """캐릭터 조회 유즈케이스"""
    
    def __init__(self, repository: CharacterRepository):
        self.repository = repository
    
    def execute(self, char_id: int) -> Optional[Character]:
        """캐릭터 조회 실행"""
        return self.repository.get_by_id(char_id)
