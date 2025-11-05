# src/domain/character.py
"""
Character 도메인 엔티티
TRPG 캐릭터의 핵심 도메인 모델
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Character:
    """TRPG 캐릭터 도메인 엔티티"""
    id: Optional[int]
    name: str
    summary: str
    detail: str
    tags: List[str]
    image: str
    created_at: Optional[int] = None
    
    # 선택적 필드
    archetype: Optional[str] = None
    background: Optional[str] = None
    scenario: Optional[str] = None
    system_prompt: Optional[str] = None
    greeting: Optional[str] = None
    world: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    
    def to_dict(self) -> dict:
        """도메인 엔티티를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "summary": self.summary,
            "detail": self.detail,
            "tags": self.tags,
            "image": self.image,
            "created_at": self.created_at,
            "archetype": self.archetype,
            "background": self.background,
            "scenario": self.scenario,
            "system_prompt": self.system_prompt,
            "greeting": self.greeting,
            "world": self.world,
            "genre": self.genre,
            "style": self.style,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """딕셔너리에서 도메인 엔티티 생성"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            detail=data.get("detail", ""),
            tags=data.get("tags", []),
            image=data.get("image", ""),
            created_at=data.get("created_at"),
            archetype=data.get("archetype"),
            background=data.get("background"),
            scenario=data.get("scenario"),
            system_prompt=data.get("system_prompt"),
            greeting=data.get("greeting"),
            world=data.get("world"),
            genre=data.get("genre"),
            style=data.get("style"),
        )
