# ========================================
# apps/api/routes/world_sessions.py — 세계관 세션 API
# - POST /v1/world-sessions/{session_id}/persona : 세션에 페르조나 적용
# ========================================

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from adapters.persistence.mongo.factory import get_mongo_client
from apps.api.deps.auth import get_current_user_from_token
from bson import ObjectId
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()


class WorldSessionPersonaApplyRequest(BaseModel):
    """세계관 세션에 페르조나 적용 요청"""
    persona_id: str


class WorldSessionPersonaApplyResponse(BaseModel):
    """세계관 세션에 페르조나 적용 응답"""
    ok: bool
    session_id: str
    persona: Dict[str, Any]


@router.post("/{session_id}/persona", summary="세계관 세션에 페르조나 적용", response_model=WorldSessionPersonaApplyResponse)
async def apply_persona_to_world_session(
    session_id: str,
    payload: WorldSessionPersonaApplyRequest,
    current_user = Depends(get_current_user_from_token),
):
    """
    세계관 세션에 페르조나를 적용합니다.
    - 세션 조회 및 권한 체크 (session.user_id == current_user.user_id)
    - user.personas에서 persona_id 찾기
    - worlds_session 문서에 persona 스냅샷 저장
    """
    try:
        if current_user is None:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
        user_id = current_user.get("google_id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="사용자 정보를 찾을 수 없습니다.")
        
        # 1) session_id를 ObjectId로 변환
        try:
            session_oid = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="잘못된 세션 ID입니다.")
        
        # 2) 세션 조회 및 권한 체크
        mongo = get_mongo_client()
        session_col = mongo["worlds_session"]
        session_doc = session_col.find_one({"_id": session_oid})
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 권한 체크: session.user_id == current_user.user_id
        session_user_id = str(session_doc.get("user_id", ""))
        if session_user_id != str(user_id):
            raise HTTPException(status_code=403, detail="이 세션에 접근할 권한이 없습니다.")
        
        # 3) user 문서에서 persona 찾기
        users_col = mongo["users"]
        try:
            user_oid = ObjectId(current_user["user_id"])
        except Exception:
            raise HTTPException(status_code=400, detail="잘못된 사용자 ID입니다.")
        
        user_doc = users_col.find_one({"_id": user_oid})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        personas = user_doc.get("personas") or []
        target_persona = None
        for p in personas:
            if p.get("persona_id") == payload.persona_id:
                target_persona = p
                break
        
        if not target_persona:
            raise HTTPException(status_code=404, detail="해당 페르조나를 찾을 수 없습니다.")
        
        # 4) persona 스냅샷 생성 (persona_id, name, gender, image_key)
        persona_snapshot = {
            "persona_id": target_persona.get("persona_id"),
            "name": target_persona.get("name"),
            "gender": target_persona.get("gender"),
            "image_key": target_persona.get("image_key"),
        }
        
        # 5) 세션 업데이트
        now = datetime.now(timezone.utc)
        session_col.update_one(
            {"_id": session_oid},
            {
                "$set": {
                    "persona": persona_snapshot,
                    "updated_at": now,
                }
            }
        )
        
        logger.info(
            "[PERSONA][APPLY][WORLD] session_id=%s user_id=%s persona_id=%s",
            session_id,
            user_id,
            payload.persona_id
        )
        
        return WorldSessionPersonaApplyResponse(
            ok=True,
            session_id=session_id,
            persona=persona_snapshot
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[PERSONA][APPLY][WORLD][ERROR] session_id=%s error=%s", session_id, str(e))
        raise HTTPException(status_code=500, detail=f"페르조나 적용 중 오류가 발생했습니다: {str(e)}")

