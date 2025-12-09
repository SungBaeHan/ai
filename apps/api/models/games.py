# ========================================
# apps/api/models/games.py — 게임 API Pydantic 모델
# ========================================

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GameRuleAttributesConfig(BaseModel):
    """게임 규칙 속성 설정"""
    enabled: bool = True
    max: int = 100
    base: int = 10


class GameRulesConfig(BaseModel):
    """게임 규칙 설정"""
    # 성공 기준/난이도
    success_base: int = 60
    difficulty_mod: Dict[str, int] = Field(
        default_factory=lambda: {"easy": -10, "normal": 0, "hard": 10, "very_hard": 20}
    )
    # 능력치 스케일
    ability_scale: float = 1.0
    # 주요 능력치 설정
    attributes: Dict[str, GameRuleAttributesConfig] = Field(default_factory=dict)
    # 주사위 설정
    dice: Dict[str, int] = Field(default_factory=dict)
    # 예: {"count": 5, "faces": 20}
    # 데미지 규칙
    damage: Dict[str, Any] = Field(default_factory=dict)
    # 예: {"str_multiplier": 1, "flat_bonus": 0, "success_bonus_scale": 1, "on_fail_zero": True}
    # 크리티컬 규칙
    critical: Dict[str, Any] = Field(default_factory=dict)
    # 예: {"threshold_ratio": 0.95, "multiplier": 2, "base_bonus_multiplier": 1.5}


class GameCharacterCreate(BaseModel):
    """게임 생성 시 캐릭터 정보"""
    char_ref_id: int
    role: Optional[str] = None


class GameCreateRequest(BaseModel):
    """게임 생성 요청 모델"""
    title: str
    world_ref_id: int
    scenario_summary: Optional[str] = None
    scenario_detail: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    characters: List[GameCharacterCreate] = Field(default_factory=list)
    rules: GameRulesConfig
    background_image_path: Optional[str] = None
    img_hash: Optional[str] = None


class WorldSnapshot(BaseModel):
    """세계관 스냅샷"""
    id: int
    name: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    img_hash: Optional[str] = None


class CharacterSnapshot(BaseModel):
    """캐릭터 스냅샷"""
    id: int
    name: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    archetype: Optional[str] = None
    attributes_base: Optional[Dict[str, Any]] = None


class GameCharacter(BaseModel):
    """게임 내 캐릭터 정보"""
    char_ref_id: int
    role: Optional[str] = None
    snapshot: CharacterSnapshot


class GameResponse(BaseModel):
    """게임 응답 모델"""
    id: int
    title: str
    world_ref_id: int
    world_snapshot: WorldSnapshot
    scenario_summary: Optional[str] = None
    scenario_detail: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    characters: List[GameCharacter] = Field(default_factory=list)
    rules: GameRulesConfig
    background_image_path: Optional[str] = None
    img_hash: Optional[str] = None
    status: str
    reg_user: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

