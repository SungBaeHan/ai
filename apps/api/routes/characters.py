# apps/api/routes/characters.py
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from packages.db import init_db, insert_character, list_characters, count_characters

# 앱 기동 시 테이블 생성
init_db()

router = APIRouter()

class CharacterIn(BaseModel):
    name: str = Field(..., description="캐릭터 이름")
    summary: str = Field(..., description="한 줄 소개")
    detail: str = Field("", description="상세 설명")
    tags: List[str] = Field(default_factory=lambda: ["TRPG", "캐릭터"])
    image: str = Field(..., description="이미지 경로 (/assets/img/char_01.png 등)")

@router.get("", summary="캐릭터 목록")
def get_list(offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=120)):
    return {
        "items": list_characters(offset, limit),
        "offset": offset,
        "limit": limit,
    }

@router.get("/count", summary="캐릭터 총 개수")
def get_count():
    return {"count": count_characters()}

@router.post("", summary="캐릭터 생성")
def create_one(body: CharacterIn):
    insert_character(body.name.strip(), body.summary.strip(), body.detail.strip(), body.tags, body.image.strip())
    return {"ok": True}
