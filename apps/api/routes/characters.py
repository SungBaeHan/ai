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
from packages.db import (                              # DB 유틸
    init_db, insert_character, list_characters, count_characters, get_character_by_id
)

init_db()                                              # 앱 기동 시 테이블 보장
router = APIRouter()                                   # 서브 라우터

class CharacterIn(BaseModel):
    """캐릭터 생성 입력 모델"""
    name: str = Field(..., description="캐릭터 이름")
    summary: str = Field(..., description="한 줄 소개")
    detail: str = Field("", description="상세 설명")
    tags: List[str] = Field(default_factory=lambda: ["TRPG", "캐릭터"])
    image: str = Field(..., description="이미지 경로 (/assets/char/xxx.png 등)")

def normalize_image(p: Optional[str]) -> str:
    """
    서버 측 이미지 경로 정규화.
    - http/https로 시작하면 그대로
    - /로 시작하면 그대로(이미 절대경로)
    - assets/... 이면 / 붙여 절대경로
    - char_*.png 또는 char/.. 패턴은 /assets/char/.. 로
    - 나머지는 /assets/img/.. 로
    """
    if not p:
        return "/assets/img/placeholder.jpg"
    s = str(p).replace("\\", "/").strip()
    if s.startswith(("http://", "https://")): return s
    if s.startswith("/"):                    return s
    if s.startswith("assets/"):              return "/" + s
    if ("/char/" in s) or s.startswith(("char/", "assets/char/", "char_")):
        if s.startswith("assets/char/"): return "/" + s
        if s.startswith("char/"):        return "/assets/" + s     # char/xxx.jpg → /assets/char/xxx.jpg
        if s.startswith("char_"):        return "/assets/char/" + s
        return "/assets/char/" + s.lstrip("/")
    return "/assets/img/" + s.lstrip("/")

@router.get("", summary="캐릭터 목록")
def get_list(offset: Optional[int] = Query(None), limit: Optional[int] = Query(None)):
    """캐릭터 목록 반환(서버가 image를 절대경로로 보정)"""
    o = 0 if offset is None else max(0, offset)
    l = 30 if limit  is None else max(1, min(120, limit))
    items = list_characters(o, l)                     # DB에서 목록
    for it in items:                                  # 이미지 경로 보정
        it["image"] = normalize_image(it.get("image"))
    return {"items": items, "offset": o, "limit": l}

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

    char = get_character_by_id(cid)                   # DB 조회
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    char["image"] = normalize_image(char.get("image"))# 이미지 경로 보정
    return char

@router.get("/count", summary="캐릭터 총 개수")
def get_count():
    """등록된 캐릭터 총 수 반환"""
    return {"count": count_characters()}

@router.post("", summary="캐릭터 생성")
def create_one(body: CharacterIn):
    """간단 생성 API(검증은 최소화)"""
    insert_character(
        body.name.strip(),
        body.summary.strip(),
        body.detail.strip(),
        body.tags,
        body.image.strip(),
    )
    return {"ok": True}
