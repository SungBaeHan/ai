# src/ports/repositories/character_repository.py
"""
CharacterRepository 포트 (인터페이스)
Dependency Inversion Principle을 위한 저장소 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.character import Character


class CharacterRepository(ABC):
    """캐릭터 저장소 인터페이스"""
    
    @abstractmethod
    def get_by_id(self, char_id: int) -> Optional[Character]:
        """ID로 캐릭터 조회"""
        pass
    
    @abstractmethod
    def list_all(self, offset: int = 0, limit: int = 30) -> List[Character]:
        """캐릭터 목록 조회"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """캐릭터 총 개수 조회"""
        pass
    
    @abstractmethod
    def create(self, character: Character) -> Character:
        """새 캐릭터 생성"""
        pass
    
    @abstractmethod
    def upsert_by_image(self, character: Character) -> Character:
        """이미지 경로로 캐릭터 upsert"""
        pass
