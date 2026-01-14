# apps/api/routes/game_turn.py
"""
게임 턴 처리 API

game_session 컬렉션 기반으로 동작합니다.
각 사용자는 owner_ref_info.user_ref_id로 구분된 자신의 세션만 조회/수정합니다.
"""

import json
import logging
from json import JSONDecodeError
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.database import Database
from adapters.persistence.mongo import get_db
from adapters.external.llm_client import get_default_llm_client
from apps.api.schemas.game_turn import (
    GameTurnRequest,
    GameTurnResponse,
    GameTurnLLMResponse,
    StatusChanges,
    UserStatusChange,
    CharacterStatusChange,
    GameSessionSnapshot,
    CharacterState,
    CombatState,
    TurnLog,
)
from apps.api.deps.user_snapshot import build_owner_ref_info
from apps.llm.prompts.trpg_game_master import (
    SYSTEM_PROMPT_TRPG,
    build_trpg_user_prompt,
)
from apps.api.deps.auth import get_current_user_from_token
from apps.api.services.game_events import (
    maybe_trigger_random_event,
    apply_event_to_session,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def extract_json(text: str) -> str:
    """
    LLM이 ```json ... ``` 같이 감싸거나, 앞뒤에 설명을 붙인 경우에도
    가능한 한 순수 JSON 부분만 잘라내는 헬퍼.
    """
    if not isinstance(text, str):
        return text

    cleaned = text.strip()

    # ```json 또는 ``` 으로 감싸진 경우 제거
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        # ```json\n{...}\n``` 형태라면 가운데 블럭을 취함
        if len(parts) >= 3:
            cleaned = parts[1]
            # "json\n{...}" 처럼 언어 토큰이 붙은 경우 제거
            if cleaned.lstrip().lower().startswith("json"):
                cleaned = cleaned.split("\n", 1)[1]
        else:
            # 그냥 ``` 로만 감싼 경우, 첫 번째와 마지막 ``` 사이를 사용
            cleaned = cleaned.replace("```", "")

    cleaned = cleaned.strip()

    # 첫 '{' 부터 마지막 '}' 까지 잘라내기 (앞뒤 잡소리 제거)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    return cleaned


def build_fallback_llm_response(raw_text: str) -> GameTurnLLMResponse:
    """
    LLM JSON 파싱에 실패했을 때,
    전체 텍스트를 narration 으로라도 써먹기 위한 fall-back 응답 생성.
    스탯 변화는 모두 0으로 처리.
    """
    # 너무 길면 앞부분만 사용 (로그형 텍스트일 수 있으니 400자 정도로 자름)
    narration = (raw_text or "").strip()
    if len(narration) > 400:
        narration = narration[:400] + "..."
    
    return GameTurnLLMResponse(
        narration=narration or "이번 턴의 설명을 불러오는 데 실패했습니다.",
        dialogues=[],  # fall-back에서는 대사 없이 상황 설명만 사용
        status_changes=StatusChanges(
            user=UserStatusChange(),
            characters=[],
        ),
    )


def _convert_game_session_to_session_snapshot(
    game_session: Dict[str, Any],
    game_id: int,
    user_id: Optional[str] = None,
) -> GameSessionSnapshot:
    """
    game_session 딕셔너리를 GameSessionSnapshot으로 변환
    """
    user_info = game_session.get("user_info", {})
    user_attrs = user_info.get("attributes", {})
    user_items = user_info.get("items", {})
    
    # 플레이어 상태 생성
    hp_attr = user_attrs.get("hp", {})
    mp_attr = user_attrs.get("mp", {})
    player = CharacterState(
        id=0,  # 플레이어는 id 0
        name="플레이어",
        hp=hp_attr.get("current", hp_attr.get("base", 100)) if isinstance(hp_attr, dict) else (hp_attr if isinstance(hp_attr, int) else 100),
        hp_max=hp_attr.get("max", 100) if isinstance(hp_attr, dict) else 100,
        mp=mp_attr.get("current", mp_attr.get("base", 0)) if isinstance(mp_attr, dict) else (mp_attr if isinstance(mp_attr, int) else 0),
        mp_max=mp_attr.get("max", 0) if isinstance(mp_attr, dict) else 0,
        gold=user_items.get("gold", 0),
        attributes=user_attrs,
    )
    
    # NPC 상태 생성
    npcs = []
    for char_info in game_session.get("characters_info", []):
        snapshot = char_info.get("snapshot", {})
        char_attrs = snapshot.get("attributes", {})
        char_items = snapshot.get("items", {})
        hp_attr = char_attrs.get("hp", {})
        mp_attr = char_attrs.get("mp", {})
        npcs.append(CharacterState(
            id=char_info.get("char_ref_id", 0),
            name=snapshot.get("name", "Unknown"),
            image_url=snapshot.get("image_url"),
            hp=hp_attr.get("current", hp_attr.get("base", 100)) if isinstance(hp_attr, dict) else (hp_attr if isinstance(hp_attr, int) else 100),
            hp_max=hp_attr.get("max", 100) if isinstance(hp_attr, dict) else 100,
            mp=mp_attr.get("current", mp_attr.get("base", 0)) if isinstance(mp_attr, dict) else (mp_attr if isinstance(mp_attr, int) else 0),
            mp_max=mp_attr.get("max", 0) if isinstance(mp_attr, dict) else 0,
            gold=char_items.get("gold", 0),
            attributes=char_attrs,
        ))
    
    # 전투 상태 생성
    combat = CombatState(
        in_combat=game_session.get("combat", {}).get("in_combat", False),
        monsters=[],  # TODO: 몬스터 정보가 있으면 변환
        phase=game_session.get("combat", {}).get("phase", "none"),
    )
    
    # 턴 로그 변환
    turn_logs = []
    for h in game_session.get("story_history", []):
        turn_num = h.get("turn", 0)
        narration = h.get("narration", "")
        if narration:
            turn_logs.append(TurnLog(
                turn=turn_num,
                speaker_type="narration",
                text=narration,
                is_action=False,
            ))
        for d in h.get("dialogues", []):
            speaker_type = d.get("speaker_type", "npc")
            # 기존 "user" -> "player"로 변환
            if speaker_type == "user":
                speaker_type = "player"
            turn_logs.append(TurnLog(
                turn=turn_num,
                speaker_type=speaker_type,
                speaker_id=d.get("char_ref_id") if speaker_type in ["npc", "monster"] else None,
                text=d.get("text", ""),
                is_action=d.get("is_action", False),
                meta=d.get("meta", {}),
            ))
    
    return GameSessionSnapshot(
        game_id=game_id,
        user_id=user_id,
        turn=game_session.get("turn", 0),
        player=player,
        npcs=npcs,
        combat=combat,
        turn_logs=turn_logs,
    )


def _convert_session_snapshot_to_game_session(
    session: GameSessionSnapshot,
    owner_ref_info: Optional[Dict[str, Any]] = None,
    world_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    GameSessionSnapshot을 game_session 딕셔너리로 변환
    """
    return {
        "game_id": session.game_id,
        "turn": session.turn,
        "user_info": {
            "attributes": {
                "hp": {
                    "current": session.player.hp,
                    "max": session.player.hp_max,
                    "base": session.player.hp,
                },
                "mp": {
                    "current": session.player.mp,
                    "max": session.player.mp_max,
                    "base": session.player.mp,
                },
                **session.player.attributes,
            },
            "items": {
                "gold": session.player.gold,
                "inventory": [],
            },
        },
        "characters_info": [
            {
                "char_ref_id": npc.id,
                "snapshot": {
                    "name": npc.name,
                    "image_url": npc.image_url,
                    "attributes": {
                        "hp": {
                            "current": npc.hp,
                            "max": npc.hp_max,
                            "base": npc.hp,
                        },
                        "mp": {
                            "current": npc.mp,
                            "max": npc.mp_max,
                            "base": npc.mp,
                        },
                        **npc.attributes,
                    },
                    "items": {
                        "gold": npc.gold,
                        "inventory": [],
                    },
                },
            }
            for npc in session.npcs
        ],
        "combat": {
            "in_combat": session.combat.in_combat,
            "monsters": [m.model_dump() for m in session.combat.monsters],
            "phase": session.combat.phase,
        },
        "story_history": [
            {
                "turn": log.turn,
                "narration": log.text if log.speaker_type == "narration" else "",
                "dialogues": [
                    {
                        "speaker_type": log.speaker_type,
                        "name": None,
                        "text": log.text,
                        "char_ref_id": log.speaker_id,
                        "is_action": log.is_action,
                        "meta": log.meta,
                    }
                ] if log.speaker_type != "narration" else [],
            }
            for log in session.turn_logs
        ],
        "world_snapshot": world_snapshot or {},  # 별도로 관리
    }
    
    # owner_ref_info가 제공되면 추가
    if owner_ref_info:
        result["owner_ref_info"] = owner_ref_info
    
    return result


# NOTE: 게임 세션 조회는 /v1/games/{game_id}/session 엔드포인트를 사용하세요.


@router.post("/{game_id}/turn", response_model=GameTurnResponse, summary="게임 턴 진행")
async def play_turn(
    game_id: int,
    payload: GameTurnRequest,
    request: Request,
    db: Database = Depends(get_db),
    current_user = Depends(get_current_user_from_token),
):
    """
    게임 턴을 진행하고 LLM 응답을 받아 상태를 업데이트합니다.
    세션 스냅샷 기반으로 동작합니다.
    """
    try:
        # 로그인 체크
        if current_user is None:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="유저 정보를 찾을 수 없습니다.")
        
        # 1) 현재 유저의 game_session 조회
        game_session = db.game_session.find_one({
            "game_id": game_id,
            "owner_ref_info.user_ref_id": user_id,
        })
        
        if not game_session:
            # 게임 메타 정보 조회
            game_doc = db.games.find_one({"id": game_id})
            if not game_doc:
                raise HTTPException(status_code=404, detail="Game not found")
            
            # 세션이 없으면 401 반환 (유효한 세션이 아님)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효한 세션이 아닙니다.",
            )
        
        # 2) 게임 메타 정보 조회
        game_doc = db.games.find_one({"id": game_id})
        if not game_doc:
            raise HTTPException(status_code=404, detail="Game not found")
        world_snapshot = game_doc.get("world_snapshot", {})
        
        # 3) 플레이어 메시지를 세션에 추가 (먼저 추가)
        # game_session dict에 직접 추가
        story_history = game_session.setdefault("story_history", [])
        current_turn = int(game_session.get("turn", 0))
        
        # 4) 랜덤 이벤트 판정 & 적용 (매 턴 주사위 굴리는 지점)
        # 개발 중에는 debug=True 고정으로 써도 괜찮고,
        # 나중엔 쿼리파라미터나 환경변수로 꺼도 됨.
        event_result, event_debug = maybe_trigger_random_event(
            game_session,
            game_doc,
            debug=True,
        )
        if event_result is not None:
            apply_event_to_session(game_session, event_result)
            # 이벤트 적용 후 턴이 증가했을 수 있으므로 다시 가져옴
            current_turn = int(game_session.get("turn", 0))
        
        # 기존 세션을 스냅샷으로 변환 (이벤트 적용 후)
        session = _convert_game_session_to_session_snapshot(game_session, game_id, user_id)
        
        # 5) LLM 엔진 입력 구성 (세션 상태 포함)
        engine_input = {
            "world": world_snapshot,
            "game_meta": {
                "id": game_doc.get("id"),
                "title": game_doc.get("title"),
                "ruleset": game_doc.get("rules", {}),
            },
            "session_state": {
                "turn": session.turn,
                "player": session.player.model_dump(),
                "npcs": [npc.model_dump() for npc in session.npcs],
                "combat": session.combat.model_dump(),
            },
            "history": [log.model_dump() for log in session.turn_logs[-20:]],  # 최근 20턴
            "user_input": payload.user_message,
            "event": event_result,  # 랜덤 이벤트 정보 전달
        }
        
        # 6) LLM 프롬프트 구성 (기존 함수 사용하되 세션 상태 포함)
        # build_trpg_user_prompt는 game_status 형태를 기대하므로 변환
        temp_session_dict = _convert_session_snapshot_to_game_session(
            session,
            owner_ref_info=game_session.get("owner_ref_info"),
            world_snapshot=world_snapshot,
        )
        user_prompt = build_trpg_user_prompt(
            game_status=temp_session_dict,  # 함수 파라미터명은 game_status지만 실제로는 game_session 데이터
            user_message=payload.user_message,
            world_snapshot=world_snapshot,
        )
        
        # 세션 상태 정보를 프롬프트에 추가
        session_state_text = f"""
[현재 세션 상태]
턴: {session.turn}
플레이어: HP {session.player.hp}/{session.player.hp_max}, MP {session.player.mp}/{session.player.mp_max}, 골드 {session.player.gold}
전투 상태: {"전투 중" if session.combat.in_combat else "평화"}
"""
        if session.npcs:
            session_state_text += "\n[NPC 상태]\n"
            for npc in session.npcs:
                session_state_text += f"- {npc.name} (ID: {npc.id}): HP {npc.hp}/{npc.hp_max}, MP {npc.mp}/{npc.mp_max}\n"
        
        if session.combat.in_combat and session.combat.monsters:
            session_state_text += "\n[몬스터 상태]\n"
            for monster in session.combat.monsters:
                session_state_text += f"- {monster.name}: HP {monster.hp}/{monster.hp_max}\n"
        
        user_prompt = session_state_text + "\n" + user_prompt
        
        # 이벤트 정보를 프롬프트에 추가
        if event_result:
            event_text = f"\n[랜덤 이벤트 발생]\n"
            event_text += f"종류: {event_result.get('kind', 'unknown')}\n"
            if event_result.get('kind') == 'combat':
                event_text += f"적 타입: {event_result.get('enemy_type', 'unknown')}\n"
                event_text += f"적들: {', '.join([e.get('name', 'Unknown') for e in event_result.get('enemies', [])])}\n"
            user_prompt = event_text + "\n" + user_prompt
        
        # 7) LLM 호출
        from apps.api.services.logging_service import (
            get_anon_id,
            get_user_id,
            get_ip_ua_ref,
            insert_event_log,
        )
        from apps.api.utils.trace import make_trace_id
        from datetime import datetime, timezone
        import time
        
        llm_client = get_default_llm_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TRPG},
            {"role": "user", "content": user_prompt},
        ]
        
        # LLM 호출 시작 이벤트
        trace_id = make_trace_id()
        llm_start_time = time.time()
        anon_id = get_anon_id(request)
        user_id_from_req = get_user_id(request)
        ip_ua_ref = get_ip_ua_ref(request)
        
        event_start_doc = {
            "ts": datetime.now(timezone.utc),
            "name": "chat_response_start",
            "source": "game",
            "anon_id": anon_id,
            "user_id": user_id_from_req,
            "path": request.url.path,
            "session_id": str(game_session.get("_id", "")),
            "entity_id": str(game_id),
            "request_id": trace_id,
            "payload": {
                "chat_type": "game",
                "turn": current_turn,
                "message_len": len(payload.user_message),
            },
        }
        insert_event_log(event_start_doc)
        
        try:
            raw_response = llm_client.generate_chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1024,  # 구조화된 JSON 응답을 위해 증가
            )
            
            # LLM 호출 성공 이벤트
            llm_duration_ms = int((time.time() - llm_start_time) * 1000)
            event_done_doc = {
                "ts": datetime.now(timezone.utc),
                "name": "chat_response_done",
                "source": "game",
                "anon_id": anon_id,
                "user_id": user_id_from_req,
                "path": request.url.path,
                "session_id": str(game_session.get("_id", "")),
                "entity_id": str(game_id),
                "request_id": trace_id,
                "payload": {
                    "chat_type": "game",
                    "turn": current_turn,
                    "latency_ms": llm_duration_ms,
                    "response_len": len(str(raw_response)),
                },
            }
            insert_event_log(event_done_doc)
        except Exception as e:
            # LLM 호출 실패 이벤트
            event_fail_doc = {
                "ts": datetime.now(timezone.utc),
                "name": "chat_response_fail",
                "source": "game",
                "anon_id": anon_id,
                "user_id": user_id_from_req,
                "path": request.url.path,
                "session_id": str(game_session.get("_id", "")),
                "entity_id": str(game_id),
                "request_id": trace_id,
                "payload": {
                    "chat_type": "game",
                    "turn": current_turn,
                    "error_type": type(e).__name__,
                },
            }
            insert_event_log(event_fail_doc)
            logger.exception(f"LLM call failed: {e}")
            raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {str(e)}")
        
        # 8) JSON 파싱
        raw_text = raw_response
        
        # 1차: 그대로 파싱 시도
        try:
            llm_data = GameTurnLLMResponse.model_validate_json(raw_text)
        except Exception as e1:
            # 2차: JSON 부분만 추출해서 재시도
            try:
                cleaned = extract_json(raw_text)
                llm_data = GameTurnLLMResponse.model_validate_json(cleaned)
            except Exception as e2:
                # 3차: 그래도 안 되면, raw_text를 narration 으로 쓰는 fall-back 생성
                logger.error("=== TRPG TURN RAW TEXT (FALLBACK) ===\n%s", raw_text)
                logger.error("=== PARSE ERROR 1 ===", exc_info=e1)
                logger.error("=== PARSE ERROR 2 ===", exc_info=e2)
                llm_data = build_fallback_llm_response(raw_text)
        
        # 7) 세션 업데이트
        # 턴 증가 (이벤트로 이미 증가했을 수 있으므로 확인)
        if event_result is None:
            session.turn += 1
        
        # 새로운 턴 로그 추가
        new_turns = []
        
        # 플레이어 메시지 추가 (먼저)
        new_turns.append(TurnLog(
            turn=session.turn,
            speaker_type="player",
            text=payload.user_message,
            is_action=False,
        ))
        
        # narration 추가
        if llm_data.narration:
            new_turns.append(TurnLog(
                turn=session.turn,
                speaker_type="narration",
                text=llm_data.narration,
                is_action=False,
            ))
        
        # dialogues 추가
        for d in llm_data.dialogues:
            speaker_type = d.speaker_type
            # 하위 호환성: "user" -> "player"
            if speaker_type == "user":
                speaker_type = "player"
            # "narration"은 이미 narration으로 추가했으므로 건너뛰기
            if speaker_type == "narration":
                continue
            new_turns.append(TurnLog(
                turn=session.turn,
                speaker_type=speaker_type,
                speaker_id=d.speaker_id if speaker_type in ["npc", "monster"] else None,
                text=d.text,
                is_action=d.is_action if hasattr(d, 'is_action') else False,
                meta=d.meta if hasattr(d, 'meta') else {},
            ))
        
        session.turn_logs.extend(new_turns)
        
        # 상태 변화 적용
        # 플레이어 상태 업데이트
        session.player.hp = max(0, min(session.player.hp_max, session.player.hp + llm_data.status_changes.user.hp_delta))
        session.player.mp = max(0, min(session.player.mp_max, session.player.mp + llm_data.status_changes.user.mp_delta))
        session.player.gold = max(0, session.player.gold + llm_data.status_changes.user.gold_delta)
        
        # NPC 상태 업데이트
        for c_change in llm_data.status_changes.characters:
            for npc in session.npcs:
                if npc.id == c_change.char_ref_id:
                    npc.hp = max(0, min(npc.hp_max, npc.hp + c_change.hp_delta))
                    npc.mp = max(0, min(npc.mp_max, npc.mp + c_change.mp_delta))
                    npc.gold = max(0, npc.gold + c_change.gold_delta)
                    break
        
        # 전투 상태 업데이트
        if llm_data.updated_combat:
            combat_data = llm_data.updated_combat
            session.combat.in_combat = combat_data.get("in_combat", session.combat.in_combat)
            session.combat.phase = combat_data.get("phase", session.combat.phase)
            
            # 몬스터 업데이트
            if "monsters" in combat_data:
                monsters_data = combat_data["monsters"]
                session.combat.monsters = [
                    CharacterState(
                        id=m.get("id", 0),
                        name=m.get("name", "Monster"),
                        hp=m.get("hp", 100),
                        hp_max=m.get("hp_max", 100),
                        mp=m.get("mp", 0),
                        mp_max=m.get("mp_max", 0),
                    )
                    for m in monsters_data
                ]
        
        # 8) 세션 저장 (game_session 컬렉션에 업데이트)
        updated_session = _convert_session_snapshot_to_game_session(
            session,
            owner_ref_info=game_session.get("owner_ref_info"),
            world_snapshot=world_snapshot,
        )
        
        # game_session 업데이트
        db.game_session.update_one(
            {
                "game_id": game_id,
                "owner_ref_info.user_ref_id": user_id,
            },
            {"$set": updated_session},
        )
        
        # 9) 응답 반환 (세션 포함하여 중복 방지)
        # characters_info 생성 (프론트엔드에서 이미지 매핑을 위해 필요)
        characters_info = []
        if updated_session and "characters_info" in updated_session:
            # game_session에서 characters_info 사용
            for char_info in updated_session["characters_info"]:
                char_ref_id = char_info.get("char_ref_id")
                snapshot = char_info.get("snapshot", {})
                if char_ref_id and snapshot:
                    characters_info.append({
                        "char_ref_id": char_ref_id,
                        "snapshot": {
                            "id": snapshot.get("id") or char_ref_id,
                            "name": snapshot.get("name", "Unknown"),
                            "image_url": snapshot.get("image_url"),
                            "attributes": snapshot.get("attributes", {}),
                        }
                    })
        else:
            # session.npcs에서 생성 (fallback)
            for npc in session.npcs:
                characters_info.append({
                    "char_ref_id": npc.id,
                    "snapshot": {
                        "name": npc.name,
                        "image_url": npc.image_url,
                        "attributes": {
                            "hp": {
                                "current": npc.hp,
                                "max": npc.hp_max,
                                "base": npc.hp,
                            },
                            "mp": {
                                "current": npc.mp,
                                "max": npc.mp_max,
                                "base": npc.mp,
                            },
                            **npc.attributes,
                        },
                        "items": {
                            "gold": npc.gold,
                            "inventory": [],
                        },
                    },
                })
        
        # 세션에 characters_info 포함
        session_dict = session.model_dump()
        session_dict["characters_info"] = characters_info
        
        return GameTurnResponse(
            game_id=game_id,
            turn=session.turn,
            narration=llm_data.narration,
            dialogues=llm_data.dialogues,
            user_info={
                "attributes": {
                    "hp": {"current": session.player.hp, "max": session.player.hp_max},
                    "mp": {"current": session.player.mp, "max": session.player.mp_max},
                },
                "items": {"gold": session.player.gold, "inventory": []},
            },
            characters_info=characters_info,
            new_turns=[log.model_dump() for log in new_turns],  # 호환성
            session=session_dict,  # 세션 전체 포함 (중복 방지)
            debug_event=event_debug,  # 디버그 정보 포함
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Game turn processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"게임 턴 처리 중 오류: {str(e)}")

