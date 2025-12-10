# apps/api/schemas/game_turn.py
"""
게임 턴 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class GameTurnRequest(BaseModel):
    """게임 턴 요청 모델"""
    user_message: str = Field(..., description="플레이어 입력 대사")


class DialogueItem(BaseModel):
    """대화 항목"""
    speaker_type: Literal["user", "npc", "system"]
    name: Optional[str] = None
    text: str


class CharacterStatusChange(BaseModel):
    """캐릭터 상태 변화"""
    char_ref_id: int
    hp_delta: int = 0
    mp_delta: int = 0
    items_add: List[str] = Field(default_factory=list)
    items_remove: List[str] = Field(default_factory=list)
    gold_delta: int = 0


class UserStatusChange(BaseModel):
    """유저 상태 변화"""
    hp_delta: int = 0
    mp_delta: int = 0
    items_add: List[str] = Field(default_factory=list)
    items_remove: List[str] = Field(default_factory=list)
    gold_delta: int = 0


class StatusChanges(BaseModel):
    """상태 변화 전체"""
    user: UserStatusChange
    characters: List[CharacterStatusChange] = Field(default_factory=list)


class GameTurnLLMResponse(BaseModel):
    """LLM에서 받은 턴 응답"""
    narration: str
    dialogues: List[DialogueItem]
    status_changes: StatusChanges


class GameTurnResponse(BaseModel):
    """프론트로 내려주는 최종 응답"""
    game_id: int
    turn: int
    narration: str
    dialogues: List[DialogueItem]
    user_info: dict
    characters_info: list

