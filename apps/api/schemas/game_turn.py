# apps/api/schemas/game_turn.py
"""
게임 턴 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class GameTurnRequest(BaseModel):
    """게임 턴 요청 모델"""
    user_message: str = Field(..., description="플레이어 입력 대사")


class DialogueItem(BaseModel):
    """대화 항목"""
    speaker_type: Literal["system", "narration", "player", "npc", "monster", "user"]  # "user"는 하위 호환성
    speaker_id: Optional[int] = None
    name: Optional[str] = None
    text: str
    is_action: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


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
    updated_combat: Optional[Dict[str, Any]] = None  # 전투 상태 업데이트 (선택적)


class GameTurnResponse(BaseModel):
    """프론트로 내려주는 최종 응답"""
    game_id: int
    turn: int
    narration: str
    dialogues: List[DialogueItem]
    user_info: dict
    characters_info: list
    session: Optional[Dict[str, Any]] = None  # 세션 전체 (중복 방지)
    new_turns: Optional[List[Dict[str, Any]]] = None  # 새 턴 로그 (호환성)
    debug_event: Optional[Dict[str, Any]] = None  # 디버그용 (옵션)


# ========================================
# 세션 스냅샷 구조 정의
# ========================================

class CharacterState(BaseModel):
    """캐릭터 상태"""
    id: int  # 캐릭터 ref id
    name: str
    image_url: Optional[str] = None
    hp: int = 100
    hp_max: int = 100
    mp: int = 0
    mp_max: int = 0
    gold: int = 0
    # 기타 스탯들
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CombatState(BaseModel):
    """전투 상태"""
    in_combat: bool = False
    monsters: List[CharacterState] = Field(default_factory=list)
    phase: Literal["none", "start", "player_turn", "npc_turn", "end"] = "none"


class TurnLog(BaseModel):
    """턴 로그"""
    turn: int
    speaker_type: Literal["system", "narration", "player", "npc", "monster"]
    speaker_id: Optional[int] = None
    text: str
    is_action: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


class GameSessionSnapshot(BaseModel):
    """게임 세션 스냅샷"""
    game_id: int
    user_id: Optional[str] = None
    turn: int = 0
    player: CharacterState
    npcs: List[CharacterState] = Field(default_factory=list)
    combat: CombatState = Field(default_factory=CombatState)
    turn_logs: List[TurnLog] = Field(default_factory=list)

