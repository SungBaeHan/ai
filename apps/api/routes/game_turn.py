# apps/api/routes/game_turn.py
"""
게임 턴 처리 API
"""

import json
import logging
from json import JSONDecodeError
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from adapters.persistence.mongo import get_db
from adapters.external.llm_client import get_default_llm_client
from apps.api.schemas.game_turn import (
    GameTurnRequest,
    GameTurnResponse,
    GameTurnLLMResponse,
    StatusChanges,
)
from apps.api.services.game_status_service import (
    get_game_status,
    save_game_status,
    apply_status_changes,
)
from apps.llm.prompts.trpg_game_master import (
    SYSTEM_PROMPT_TRPG,
    build_trpg_user_prompt,
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


@router.post("/{game_id}/turn", response_model=GameTurnResponse, summary="게임 턴 진행")
async def play_turn(
    game_id: int,
    payload: GameTurnRequest,
    db: Database = Depends(get_db),
):
    """
    게임 턴을 진행하고 LLM 응답을 받아 상태를 업데이트합니다.
    """
    try:
        # 1) 게임 상태 조회
        game_status = get_game_status(db, game_id)
        if not game_status:
            # 게임이 없으면 초기 상태 생성
            # 먼저 게임 메타 정보 조회
            game_doc = db.games.find_one({"id": game_id})
            if not game_doc:
                raise HTTPException(status_code=404, detail="Game not found")
            
            # 초기 게임 상태 생성
            game_status = {
                "game_id": game_id,
                "turn": 0,
                "user_info": {
                    "attributes": {},
                    "items": {"gold": 0, "inventory": []},
                },
                "characters_info": [],
                "story_history": [],
                "world_snapshot": game_doc.get("world_snapshot", {}),
            }
            
            # 게임의 캐릭터 정보를 characters_info로 복사
            if "characters" in game_doc:
                for char in game_doc["characters"]:
                    char_info = {
                        "char_ref_id": char.get("char_ref_id"),
                        "snapshot": char.get("snapshot", {}),
                    }
                    # 초기 속성 설정 (rules.attributes 기반)
                    if "attributes_base" in char.get("snapshot", {}):
                        char_info["snapshot"]["attributes"] = {}
                        for attr_name, attr_config in char.get("snapshot", {}).get("attributes_base", {}).items():
                            if isinstance(attr_config, dict):
                                char_info["snapshot"]["attributes"][attr_name] = {
                                    "max": attr_config.get("max", 100),
                                    "base": attr_config.get("base", 10),
                                    "current": attr_config.get("base", 10),
                                }
                    game_status["characters_info"].append(char_info)
            
            # 초기 상태 저장
            save_game_status(db, game_status)
        
        # 2) world_snapshot 가져오기
        world_snapshot = game_status.get("world_snapshot", {})
        if not world_snapshot:
            # 게임 메타에서 가져오기
            game_doc = db.games.find_one({"id": game_id})
            if game_doc:
                world_snapshot = game_doc.get("world_snapshot", {})
                game_status["world_snapshot"] = world_snapshot
        
        # 3) LLM 프롬프트 구성
        user_prompt = build_trpg_user_prompt(
            game_status=game_status,
            user_message=payload.user_message,
            world_snapshot=world_snapshot,
        )
        
        # 4) LLM 호출
        llm_client = get_default_llm_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TRPG},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            raw_response = llm_client.generate_chat_completion(
                messages=messages,
                model="gpt-4o-mini",  # 또는 프로젝트 설정에 맞게
                temperature=0.7,
            )
        except Exception as e:
            logger.exception(f"LLM call failed: {e}")
            raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {str(e)}")
        
        # 5) JSON 파싱
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
                # 디버깅을 위해 raw_text도 로깅 후, 친절한 에러 메시지로 래핑
                logger.error("=== TRPG TURN RAW TEXT ===")
                logger.error(raw_text)
                logger.error("=== PARSE ERROR 1 ===", exc_info=e1)
                logger.error("=== PARSE ERROR 2 ===", exc_info=e2)
                raise HTTPException(
                    status_code=500,
                    detail=f"Turn 응답 JSON 1차/2차 validation error: {str(e2)}",
                )
        
        # 6) 턴 증가
        current_turn = int(game_status.get("turn", 0)) + 1
        game_status["turn"] = current_turn
        
        # 7) story_history에 추가
        history_item = {
            "turn": current_turn,
            "narration": llm_data.narration,
            "dialogues": [d.model_dump() for d in llm_data.dialogues],
        }
        game_status.setdefault("story_history", []).append(history_item)
        
        # 8) 상태 변화 적용
        game_status = apply_status_changes(game_status, llm_data.status_changes)
        
        # 9) 게임 상태 저장
        save_game_status(db, game_status)
        
        # 10) 응답 반환
        return GameTurnResponse(
            game_id=game_id,
            turn=current_turn,
            narration=llm_data.narration,
            dialogues=llm_data.dialogues,
            user_info=game_status.get("user_info", {}),
            characters_info=game_status.get("characters_info", []),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Game turn processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"게임 턴 처리 중 오류: {str(e)}")

