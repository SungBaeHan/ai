# apps/api/services/game_events.py
import random
from typing import Optional, Literal, Dict, Any, List, Tuple

AreaType = Literal["town", "field", "dungeon"]
EnemyType = Literal["bandits", "monsters", "soldiers"]


def get_area_type(session: dict) -> AreaType:
    """
    TODO: 나중에 세션/스토리/월드 정보 보고 실제 지역을 판정한다.
    지금은 일단 'field' 고정.
    """
    return "field"


def maybe_trigger_random_event(
    session: dict,
    game_meta: dict,
    debug: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    매 턴마다 호출해서 랜덤 이벤트(전투 등)를 결정하는 함수.
    - debug=False: (event, None)
    - debug=True:  (event, debug_info)
    """
    rules = game_meta.get("rules", {})
    event_rules = rules.get("events", {})

    # 기본 이벤트 확률 (%)
    base_chance: int = int(event_rules.get("base_chance", 0))

    # 지역 타입 및 보정치
    area_type: AreaType = get_area_type(session)
    area_mods: Dict[str, int] = event_rules.get("area_mod", {})
    area_mod: int = int(area_mods.get(area_type, 0))

    # 최종 확률 (0~100으로 클램프)
    chance = max(0, min(100, base_chance + area_mod))

    # 1~100 사이 주사위
    roll = random.randint(1, 100)

    debug_info: Optional[Dict[str, Any]] = None
    if debug:
        debug_info = {
            "area": area_type,
            "base_chance": base_chance,
            "area_mod": area_mod,
            "chance": chance,
            "roll": roll,
            "triggered": False,
            "enemy_type": None,
        }

    # 실패 시 이벤트 없음
    if roll > chance:
        return None, debug_info

    # 어떤 종류의 전투인지 가중치로 선택
    combat_weights: Dict[str, int] = event_rules.get("combat_weights", {})
    enemy_type: EnemyType = _choose_enemy_type(combat_weights)

    enemies: List[Dict[str, Any]] = _build_enemy_group(enemy_type, rules)

    event = {
        "kind": "combat",
        "area": area_type,
        "enemy_type": enemy_type,
        "enemies": enemies,
        "roll": roll,
        "chance": chance,
    }

    if debug_info is not None:
        debug_info["triggered"] = True
        debug_info["enemy_type"] = enemy_type

    return event, debug_info


def _choose_enemy_type(weights: Dict[str, int]) -> EnemyType:
    """
    {"bandits": 40, "monsters": 40, "soldiers": 20} 를 가중치 랜덤 선택.
    """
    if not weights:
        return "monsters"

    total = sum(max(0, int(w)) for w in weights.values())
    if total <= 0:
        return "monsters"

    r = random.randint(1, total)
    cumulative = 0
    for key, w in weights.items():
        cumulative += max(0, int(w))
        if r <= cumulative:
            return key  # type: ignore[return-value]

    return "monsters"


def _build_enemy_group(enemy_type: EnemyType, rules: dict) -> List[Dict[str, Any]]:
    """
    간단한 적 그룹 구성. 나중에는 몬스터 메타 테이블로 분리 가능.
    지금은 타입별로 하드코딩.
    """
    # TODO: rules 안에 몬스터 정의가 들어가면 여기서 참조하도록 확장.
    if enemy_type == "bandits":
        return [
            {"name": "산적", "hp": 30, "attack": 5},
            {"name": "산적 두목", "hp": 50, "attack": 8},
        ]
    if enemy_type == "soldiers":
        return [
            {"name": "적국 보병", "hp": 35, "attack": 6},
            {"name": "적국 궁수", "hp": 25, "attack": 7},
        ]

    # 기본 몬스터
    return [
        {"name": "슬라임", "hp": 20, "attack": 4},
        {"name": "고블린", "hp": 25, "attack": 5},
    ]


def apply_event_to_session(session: dict, event: Dict[str, Any]) -> None:
    """
    maybe_trigger_random_event() 결과를 실제 세션 상태에 반영한다.
    """
    if event.get("kind") != "combat":
        return

    # combat 상태 세팅
    session.setdefault("combat", {})
    session["combat"]["in_combat"] = True
    session["combat"]["phase"] = "start"
    session["combat"]["monsters"] = event["enemies"]

    # 턴 증가 및 스토리 로그 추가
    story = session.setdefault("story_history", [])
    current_turn = int(session.get("turn", 0)) + 1
    session["turn"] = current_turn

    narration = f"갑작스럽게 {event['enemy_type']}와(과)의 전투가 시작됩니다!"
    story.append({
        "turn": current_turn,
        "narration": narration,
        "dialogues": [],
        "meta": {
            "event": "combat_start",
            "enemy_type": event["enemy_type"],
            "roll": event["roll"],
            "chance": event["chance"],
        },
    })
