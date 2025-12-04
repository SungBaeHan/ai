# ========================================
# apps/api/routes/worlds.py — 세계관 API
# - POST /v1/worlds/upload-image : 이미지 업로드
# - POST /v1/worlds/ai-detail    : AI 상세 생성
# - POST /v1/worlds              : 세계관 생성
# ========================================

import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from adapters.persistence.mongo import get_db
from adapters.file_storage.r2_storage import R2Storage
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger(__name__)

router = APIRouter()                                   # 서브 라우터

# R2 Storage 인스턴스 (지연 초기화)
_r2_storage: Optional[R2Storage] = None

def get_r2_storage() -> R2Storage:
    """R2 Storage 싱글톤 인스턴스 반환"""
    global _r2_storage
    if _r2_storage is None:
        try:
            _r2_storage = R2Storage()
        except Exception as e:
            logger.error(f"Failed to initialize R2Storage: {e}")
            raise HTTPException(status_code=500, detail="R2 storage not configured")
    return _r2_storage

# === 이미지 업로드 ===
@router.post("/upload-image", summary="세계관 이미지 업로드")
async def upload_world_image(file: UploadFile = File(...)):
    """
    세계관 생성 화면에서 대표 이미지를 업로드하면 R2에 저장하고 URL과 메타를 반환
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Content-Type 확인
        content_type = file.content_type or "image/png"
        if not content_type.startswith("image/"):
            content_type = "image/png"
        
        # R2에 업로드
        r2 = get_r2_storage()
        meta = r2.upload_image(content, prefix="assets/world/", content_type=content_type)
        
        return {
            "image": meta["url"],
            "src_file": meta["src_file"],
            "img_hash": meta["img_hash"],
            "key": meta["key"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# === AI 상세 생성 ===
class WorldBaseInfo(BaseModel):
    """세계관 기본 정보 (AI 생성용)"""
    name: str
    genre: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class WorldDetailResponse(BaseModel):
    """AI 생성된 세계관 상세 정보"""
    detail: str
    regions: List[str]
    factions: List[str]
    conflicts: str
    opening_scene: str
    style: str

@router.post("/ai-detail", response_model=WorldDetailResponse, summary="AI로 세계관 상세 생성")
async def ai_generate_world_detail(payload: WorldBaseInfo):
    """
    세계관 기본 정보를 바탕으로 상세 설정을 AI가 생성합니다.
    """
    try:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="World name is required")
        
        # 프롬프트 구성
        tags_str = ", ".join(payload.tags) if payload.tags else "없음"
        prompt = f"""다음 정보를 바탕으로 TRPG 세계관의 상세 설정을 생성해주세요.

세계관 이름: {payload.name}
장르: {payload.genre or "미정"}
한 줄 요약: {payload.summary or "없음"}
태그: {tags_str}

다음 JSON 형식으로 응답해주세요:
{{
  "detail": "세계관의 전반적인 설명 (3-5문장)",
  "regions": ["지역1", "지역2", "지역3"],
  "factions": ["세력1", "세력2", "세력3"],
  "conflicts": "주요 갈등과 대립 구조 (3-5문장)",
  "opening_scene": "TRPG 시작 장면 설명 (3-5문장)",
  "style": "세계관의 톤과 분위기 (예: 어둡고 신비로운 분위기, 마법과 기술이 공존하는 세계)"
}}

반드시 유효한 JSON만 반환하고, 다른 설명은 포함하지 마세요."""
        
        # OpenAI 호출
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates TRPG world details in JSON format. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.invoke(messages)
        content = getattr(response, "content", str(response))
        
        # JSON 파싱
        try:
            # JSON 코드 블록 제거 (```json ... ```)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {content[:200]}")
            # 기본값 반환
            data = {
                "detail": f"{payload.name}의 세계관 설명입니다.",
                "regions": ["주요 지역1", "주요 지역2"],
                "factions": ["주요 세력1", "주요 세력2"],
                "conflicts": "주요 갈등 구조입니다.",
                "opening_scene": "모험이 시작되는 장면입니다.",
                "style": "판타지 분위기",
            }
        
        return WorldDetailResponse(
            detail=data.get("detail", ""),
            regions=data.get("regions", []),
            factions=data.get("factions", []),
            conflicts=data.get("conflicts", ""),
            opening_scene=data.get("opening_scene", ""),
            style=data.get("style", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("AI generation failed")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# === 세계관 생성 ===
class WorldCreatePayload(BaseModel):
    """세계관 생성 전체 필드"""
    name: str
    genre: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []
    image: str
    src_file: Optional[str] = None
    img_hash: Optional[str] = None
    detail: Optional[str] = None
    regions: Optional[List[str]] = None
    factions: Optional[List[str]] = None
    conflicts: Optional[str] = None
    opening_scene: Optional[str] = None
    style: Optional[str] = None

@router.post("", summary="세계관 생성")
def create_world(payload: WorldCreatePayload):
    """
    세계관 생성 화면에서 모든 값을 모아 MongoDB worlds 컬렉션에 새 문서로 저장
    """
    try:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="World name is required")
        if not payload.image.strip():
            raise HTTPException(status_code=400, detail="Image is required")
        
        # MongoDB에서 최대 id 찾기
        db = get_db()
        col = db["worlds"]
        max_doc = col.find_one(sort=[("id", -1)])
        next_id = (max_doc["id"] if max_doc and "id" in max_doc else 0) + 1
        
        now = int(time.time())
        
        # 문서 생성
        doc = {
            "id": next_id,
            "name": payload.name.strip(),
            "genre": payload.genre,
            "summary": payload.summary or "",
            "tags": payload.tags or [],
            "image": payload.image.strip(),
            "src_file": payload.src_file,
            "img_hash": payload.img_hash,
            "detail": payload.detail or "",
            "regions": payload.regions or [],
            "factions": payload.factions or [],
            "conflicts": payload.conflicts or "",
            "opening_scene": payload.opening_scene or "",
            "style": payload.style or "",
            "created_at": now,
            "updated_at": now,
        }
        
        col.insert_one(doc)
        
        return {
            "ok": True,
            "id": next_id,
            "world": doc
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("World creation failed")
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")

