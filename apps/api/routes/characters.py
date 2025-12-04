# ========================================
# apps/api/routes/characters.py — 캐릭터 API
# - GET /v1/characters           : 목록
# - GET /v1/characters/{id}      : 단일(숫자 또는 char_XX 모두 허용)
# - GET /v1/characters/count     : 총 개수
# - POST /v1/characters          : 생성(전체 필드)
# - POST /v1/characters/upload-image : 이미지 업로드
# - POST /v1/characters/ai-detail    : AI 상세 생성
# 서버에서 image 값을 항상 절대경로(/assets/...)로 정규화해서 내려줌
# ========================================

import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from adapters.persistence.factory import get_character_repo
from adapters.persistence.mongo import get_db
from src.domain.character import Character
from apps.api.utils import build_public_image_url
from adapters.file_storage.r2_storage import R2Storage
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger(__name__)

router = APIRouter()                                   # 서브 라우터
repo = get_character_repo()                            # Repository 인터페이스를 통한 접근

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

# === 이미지 경로 정규화 ===
def normalize_image(path: str | None) -> str | None:
    """
    이미지 경로를 R2 public URL로 변환합니다.
    
    - 이미 전체 URL인 경우 그대로 반환
    - 파일명을 추출하여 /assets/char/ 접두사를 사용한 R2 public URL 생성
    """
    return build_public_image_url(path)

class CharacterIn(BaseModel):
    """캐릭터 생성 입력 모델"""
    name: str = Field(..., description="캐릭터 이름")
    summary: str = Field(..., description="한 줄 소개")
    detail: str = Field("", description="상세 설명")
    tags: List[str] = Field(default_factory=lambda: ["TRPG", "캐릭터"])
    image: str = Field(..., description="이미지 경로 (/assets/char/xxx.png 등)")

@router.get("", summary="캐릭터 목록")
def get_list(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1), q: str = Query(None)):
    """캐릭터 목록 반환(서버가 image를 절대경로로 보정)"""
    # MongoDB 어댑터에만 list_paginated가 있을 수 있으므로 getattr로 안전 호출
    fn = getattr(repo, "list_paginated", None)
    if callable(fn):
        try:
            result = fn(skip=skip, limit=limit, q=q)
            items = result.get("items", [])
            for it in items:
                it["image"] = normalize_image(it.get("image"))
            return {
                "items": items,
                "total": result.get("total", len(items)),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            print(f"[WARN] Repository list_paginated failed: {e}. Falling back to list_all.")
    
    # Repository 인터페이스의 list_all 사용 (fallback)
    offset = skip
    l = max(1, min(120, limit))
    characters = repo.list_all(offset=offset, limit=l)
    items = []
    for char in characters:
        char_dict = char.to_dict()
        char_dict["image"] = normalize_image(char_dict.get("image"))
        # 프론트엔드 호환성을 위해 summary를 shortBio로도 매핑
        if "summary" in char_dict and "shortBio" not in char_dict:
            char_dict["shortBio"] = char_dict["summary"]
        # detail을 longBio로도 매핑
        if "detail" in char_dict and "longBio" not in char_dict:
            char_dict["longBio"] = char_dict["detail"]
        items.append(char_dict)
    return {"items": items, "total": len(items), "skip": skip, "limit": l}

@router.get("/{character_id}", summary="캐릭터 단일 조회")
def get_one(character_id: str):
    """
    단일 캐릭터 조회
    - '6' 또는 'char_06' 모두 허용
    """
    cid = character_id
    if isinstance(cid, str) and cid.startswith("char_"):
        # 'char_06' → 6
        try:
            cid = int(cid.split("_", 1)[1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid character id")
    try:
        cid = int(cid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid character id")

    # Repository 인터페이스를 통한 조회
    char = repo.get_by_id(cid)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_dict = char.to_dict()
    char_dict["image"] = normalize_image(char_dict.get("image"))
    # 프론트엔드 호환성을 위해 summary를 shortBio로도 매핑
    if "summary" in char_dict and "shortBio" not in char_dict:
        char_dict["shortBio"] = char_dict["summary"]
    # detail을 longBio로도 매핑
    if "detail" in char_dict and "longBio" not in char_dict:
        char_dict["longBio"] = char_dict["detail"]
    return char_dict

@router.get("/count", summary="캐릭터 총 개수")
def get_count():
    """등록된 캐릭터 총 수 반환"""
    # Repository 인터페이스를 통한 조회
    return {"count": repo.count()}

# === 이미지 업로드 ===
@router.post("/upload-image", summary="캐릭터 이미지 업로드")
async def upload_character_image(file: UploadFile = File(...)):
    """
    캐릭터 생성 화면에서 대표 이미지를 업로드하면 R2에 저장하고 URL과 메타를 반환
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
        meta = r2.upload_image(content, prefix="assets/char/", content_type=content_type)
        
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
class CharacterBaseInfo(BaseModel):
    """캐릭터 기본 정보 (AI 생성용)"""
    name: str
    archetype: Optional[str] = None
    world: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []

class CharacterDetailResponse(BaseModel):
    """AI 생성된 캐릭터 상세 정보"""
    background: str
    detail: str
    greeting: str
    style: str
    persona_traits: List[str]
    examples: List[Dict[str, str]]
    scenario: str
    system_prompt: str

@router.post("/ai-detail", response_model=CharacterDetailResponse, summary="AI로 캐릭터 상세 생성")
async def ai_generate_character_detail(payload: CharacterBaseInfo):
    """
    캐릭터 기본 정보를 바탕으로 상세 설정을 AI가 생성합니다.
    """
    try:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="Character name is required")
        
        # 프롬프트 구성
        tags_str = ", ".join(payload.tags) if payload.tags else "없음"
        prompt = f"""다음 정보를 바탕으로 TRPG 캐릭터의 상세 설정을 생성해주세요.

캐릭터 이름: {payload.name}
아키타입/직업: {payload.archetype or "미정"}
소속 세계관: {payload.world or "미정"}
한 줄 요약: {payload.summary or "없음"}
태그: {tags_str}

다음 JSON 형식으로 응답해주세요:
{{
  "background": "캐릭터의 배경 스토리와 과거 (3-5문장)",
  "detail": "성격과 특징에 대한 상세 설명 (3-5문장)",
  "greeting": "첫 만남 시 인사말 (1문장, 구어체)",
  "style": "말투와 톤 설명 (예: 시크하고 간결한 톤, 현장 보고체)",
  "persona_traits": ["특징1", "특징2", "특징3"],
  "examples": [
    {{"user": "사용자 대사 예시", "assistant": "캐릭터 응답 예시"}},
    {{"user": "사용자 대사 예시2", "assistant": "캐릭터 응답 예시2"}}
  ],
  "scenario": "TRPG 시작 장면 설명 (2-3문장)",
  "system_prompt": "캐릭터의 행동과 말투를 지시하는 시스템 프롬프트 (2-3문장)"
}}

반드시 유효한 JSON만 반환하고, 다른 설명은 포함하지 마세요."""
        
        # OpenAI 호출
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates TRPG character details in JSON format. Always respond with valid JSON only."},
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
                "background": f"{payload.name}의 배경 스토리입니다.",
                "detail": f"{payload.name}의 성격과 특징입니다.",
                "greeting": "안녕하세요.",
                "style": "자연스러운 구어체",
                "persona_traits": ["친절함", "책임감"],
                "examples": [
                    {"user": "안녕", "assistant": "안녕하세요."}
                ],
                "scenario": "모험이 시작됩니다.",
                "system_prompt": f"{payload.name}의 행동과 말투를 유지하세요."
            }
        
        return CharacterDetailResponse(
            background=data.get("background", ""),
            detail=data.get("detail", ""),
            greeting=data.get("greeting", ""),
            style=data.get("style", ""),
            persona_traits=data.get("persona_traits", []),
            examples=data.get("examples", []),
            scenario=data.get("scenario", ""),
            system_prompt=data.get("system_prompt", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("AI generation failed")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# === 캐릭터 생성 (전체 필드) ===
class CharacterCreatePayload(BaseModel):
    """캐릭터 생성 전체 필드"""
    name: str
    archetype: Optional[str] = None
    world: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []
    image: str
    src_file: Optional[str] = None
    img_hash: Optional[str] = None
    background: Optional[str] = None
    detail: Optional[str] = None
    greeting: Optional[str] = None
    style: Optional[str] = None
    persona_traits: Optional[List[str]] = None
    examples: Optional[List[Dict[str, str]]] = None
    scenario: Optional[str] = None
    system_prompt: Optional[str] = None

@router.post("", summary="캐릭터 생성 (전체 필드)")
def create_character(payload: CharacterCreatePayload):
    """
    캐릭터 생성 화면에서 모든 값을 모아 MongoDB characters 컬렉션에 새 문서로 저장
    """
    try:
        if not payload.name.strip():
            raise HTTPException(status_code=400, detail="Character name is required")
        if not payload.image.strip():
            raise HTTPException(status_code=400, detail="Image is required")
        
        # MongoDB에서 최대 id 찾기
        db = get_db()
        col = db["characters"]
        max_doc = col.find_one(sort=[("id", -1)])
        next_id = (max_doc["id"] if max_doc and "id" in max_doc else 0) + 1
        
        now = int(time.time())
        
        # Character 도메인 엔티티 생성
        character = Character(
            id=next_id,
            name=payload.name.strip(),
            summary=payload.summary or "",
            detail=payload.detail or "",
            tags=payload.tags or [],
            image=payload.image.strip(),
            created_at=now,
            updated_at=now,
            archetype=payload.archetype,
            background=payload.background,
            scenario=payload.scenario,
            system_prompt=payload.system_prompt,
            greeting=payload.greeting,
            world=payload.world,
            style=payload.style,
            persona_traits=payload.persona_traits,
            examples=payload.examples,
            src_file=payload.src_file,
            img_hash=payload.img_hash,
        )
        
        # Repository를 통한 저장
        repo.create(character)
        
        return {
            "ok": True,
            "id": next_id,
            "character": character.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Character creation failed")
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")
