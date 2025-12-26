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
    persona_traits: Optional[List[str]] = None
    examples: Optional[List[dict]] = None
    src_file: Optional[str] = None
    img_hash: Optional[str] = None
    updated_at: Optional[int] = None
    gender: Optional[str] = None  # male/female/none
    
    def to_dict(self) -> dict:
        """도메인 엔티티를 딕셔너리로 변환"""
        result = {
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
        # None이 아닌 필드만 추가
        if self.persona_traits is not None:
            result["persona_traits"] = self.persona_traits
        if self.examples is not None:
            result["examples"] = self.examples
        if self.src_file is not None:
            result["src_file"] = self.src_file
        if self.img_hash is not None:
            result["img_hash"] = self.img_hash
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at
        if self.gender is not None:
            result["gender"] = self.gender
        return result
    
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
            persona_traits=data.get("persona_traits"),
            examples=data.get("examples"),
            src_file=data.get("src_file"),
            img_hash=data.get("img_hash"),
            updated_at=data.get("updated_at"),
            gender=data.get("gender"),
        )
