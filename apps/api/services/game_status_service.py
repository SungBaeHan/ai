# apps/api/services/game_status_service.py
"""
게임 상태 관리 서비스
"""

from typing import Optional, Dict, Any
from pymongo.database import Database
from apps.api.schemas.game_turn import StatusChanges
import logging

logger = logging.getLogger(__name__)

COLLECTION_NAME = "game_status"


def get_game_status(db: Database, game_id: int) -> Optional[Dict[str, Any]]:
    """
    게임 상태 조회
    
    Args:
        db: MongoDB 데이터베이스
        game_id: 게임 ID
    
    Returns:
        게임 상태 딕셔너리 또는 None
    """
    doc = db[COLLECTION_NAME].find_one({"game_id": game_id})
    if doc and "_id" in doc:
        doc.pop("_id", None)
    return doc


def save_game_status(db: Database, game_status: Dict[str, Any]):
    """
    게임 상태 저장 (upsert)
    
    Args:
        db: MongoDB 데이터베이스
        game_status: 게임 상태 딕셔너리
    """
    game_id = game_status.get("game_id")
    if not game_id:
        raise ValueError("game_status must contain 'game_id'")
    
    db[COLLECTION_NAME].update_one(
        {"game_id": game_id},
        {"$set": game_status},
        upsert=True,
    )


def apply_status_changes(game_status: Dict[str, Any], changes: StatusChanges) -> Dict[str, Any]:
    """
    상태 변화를 게임 상태에 적용
    
    Args:
        game_status: 현재 게임 상태
        changes: 적용할 상태 변화
    
    Returns:
        업데이트된 게임 상태
    """
    # 1) user 적용
    user_info = game_status.setdefault("user_info", {})
    user_attr = user_info.setdefault("attributes", {})
    user_items = user_info.setdefault("items", {"gold": 0, "inventory": []})
    
    def apply_attr(attr_dict: Dict[str, Any], key: str, delta: int):
        """속성 값 변경 적용"""
        if key not in attr_dict:
            return
        attr = attr_dict[key]
        if isinstance(attr, dict):
            current = attr.get("current", attr.get("base", 0))
            max_val = attr.get("max", 100)
            new_current = max(0, min(max_val, current + delta))
            attr["current"] = new_current
        else:
            # 단순 숫자인 경우
            attr_dict[key] = max(0, attr_dict[key] + delta)
    
    # HP/MP 적용
    apply_attr(user_attr, "hp", changes.user.hp_delta)
    apply_attr(user_attr, "mp", changes.user.mp_delta)
    
    # 골드 및 아이템 적용
    user_items["gold"] = max(0, user_items.get("gold", 0) + changes.user.gold_delta)
    inventory = user_items.setdefault("inventory", [])
    
    for item in changes.user.items_add:
        if item not in inventory:
            inventory.append(item)
    
    for item in changes.user.items_remove:
        if item in inventory:
            inventory.remove(item)
    
    # 2) 각 캐릭터 적용
    char_list = game_status.setdefault("characters_info", [])
    
    for c_change in changes.characters:
        for c in char_list:
            if c.get("char_ref_id") == c_change.char_ref_id:
                snapshot = c.setdefault("snapshot", {})
                c_attr = snapshot.setdefault("attributes", {})
                c_items = snapshot.setdefault("items", {"gold": 0, "inventory": []})
                
                # HP/MP 적용
                apply_attr(c_attr, "hp", c_change.hp_delta)
                apply_attr(c_attr, "mp", c_change.mp_delta)
                
                # 골드 및 아이템 적용
                c_items["gold"] = max(0, c_items.get("gold", 0) + c_change.gold_delta)
                c_inventory = c_items.setdefault("inventory", [])
                
                for item in c_change.items_add:
                    if item not in c_inventory:
                        c_inventory.append(item)
                
                for item in c_change.items_remove:
                    if item in c_inventory:
                        c_inventory.remove(item)
                break
    
    return game_status

