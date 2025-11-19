# ========================================
# apps/api/routes/characters.py — 캐릭터 API
# - GET /v1/characters           : 목록
# - GET /v1/characters/{id}      : 단일(숫자 또는 char_XX 모두 허용)
# - GET /v1/characters/count     : 총 개수
# - POST /v1/characters          : 생성(간단)
# 서버에서 image 값을 항상 절대경로(/assets/...)로 정규화해서 내려줌
# ========================================

from typing import List, Optional                      # 타입 힌트
from fastapi import APIRouter, Query, HTTPException    # 라우터/쿼리/에러
from pydantic import BaseModel, Field                  # 바디 검증 모델
from adapters.persistence.factory import get_character_repo
from src.domain.character import Character
from apps.api.utils import build_r2_public_url

router = APIRouter()                                   # 서브 라우터
repo = get_character_repo()                            # Repository 인터페이스를 통한 접근

# === 이미지 경로 정규화 ===
def normalize_image(path: str | None) -> str | None:
    """
    이미지 경로를 R2 public URL로 변환합니다.
    
    - 이미 전체 URL인 경우 그대로 반환
    - 상대 경로('/assets/...')인 경우 R2_PUBLIC_BASE_URL을 사용하여 R2 public URL 생성
    """
    return build_r2_public_url(path)

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

@router.post("", summary="캐릭터 생성")
def create_one(body: CharacterIn):
    """간단 생성 API(검증은 최소화)"""
    # Repository 인터페이스를 통한 생성
    import time
    character = Character(
        id=None,
        name=body.name.strip(),
        summary=body.summary.strip(),
        detail=body.detail.strip(),
        tags=body.tags,
        image=body.image.strip(),
        created_at=int(time.time())
    )
    repo.create(character)
    return {"ok": True}
