# apps/api/services/game_session.py
"""
게임 세션 관련 유틸리티 함수
"""

from typing import Any, Dict, List


def build_initial_characters_info(game: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    games 컬렉션의 game 문서에서 NPC 정보를 읽어
    game_session.characters_info 초기 값을 만들어준다.
    """
    characters_info: List[Dict[str, Any]] = []

    chars = game.get("characters") or []
    rules_attr = (game.get("rules") or {}).get("attributes") or {}

    for ch in chars:
        snapshot = ch.get("snapshot") or {}
        base_attr = snapshot.get("attributes_base") or {}

        # HP / MP 기본값 계산
        attrs: Dict[str, Any] = {}
        for key in ("hp", "mp"):
            src = base_attr.get(key) or rules_attr.get(key) or {}
            if src and not src.get("enabled", True):
                continue

            base = src.get("base", src.get("max", 0) or 0)
            max_ = src.get("max", base or 0)
            attrs[key] = {
                "current": base or max_ or 0,
                "max": max_,
                "base": base or max_ or 0,
            }

        # 혹시 아무것도 안들어갔으면 안전한 기본값
        if not attrs:
            attrs = {
                "hp": {"current": 100, "max": 100, "base": 100},
                "mp": {"current": 80, "max": 80, "base": 80},
            }

        characters_info.append(
            {
                "char_ref_id": ch.get("char_ref_id"),
                "snapshot": {
                    "name": snapshot.get("name"),
                    "image_url": snapshot.get("image_url"),
                    "attributes": attrs,
                    "items": {
                        "gold": 0,
                        "inventory": [],
                    },
                },
            }
        )

    return characters_info
