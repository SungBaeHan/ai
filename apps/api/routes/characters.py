# ========================================
# apps/api/routes/characters.py — 주석 추가 상세 버전
# 캐릭터 목록/카운트/생성 API. 웹 UI(home.html)가 /v1/characters를 호출해 목록을 가져간다.
# ========================================

from typing import List                         # 타입 힌트: 리스트
from fastapi import APIRouter, Query            # 라우터 및 쿼리 파라미터
from pydantic import BaseModel, Field           # 입력 데이터 모델 정의
from typing import Optional                     # Optional 타입 사용

# DB 유틸 함수들: 테이블 초기화/삽입/조회/카운트
from packages.db import init_db, insert_character, list_characters, count_characters

# 애플리케이션 기동 시 테이블 생성 보장
init_db()

# 라우터 인스턴스
router = APIRouter()

class CharacterIn(BaseModel):
    """POST /v1/characters 바디 스키마 정의"""
    name: str = Field(..., description="캐릭터 이름")                   # 필수: 이름
    summary: str = Field(..., description="한 줄 소개")                 # 필수: 요약
    detail: str = Field("", description="상세 설명")                    # 선택: 상세
    tags: List[str] = Field(default_factory=lambda: ["TRPG", "캐릭터"]) # 기본 태그 목록
    image: str = Field(..., description="이미지 경로 (/assets/img/char_01.png 등)")  # 필수 이미지 경로

@router.get("", summary="캐릭터 목록")
def get_list(
    offset: Optional[int] = Query(None),        # 페이지 시작 오프셋
    limit: Optional[int] = Query(None)          # 페이지 크기
):
    """캐릭터 목록을 페이징하여 반환한다."""
    o = 0 if offset is None else max(0, offset) # 음수 방지
    l = 30 if limit is None else max(1, min(120, limit))  # 1~120 사이 제한 (기본 30)
    return {
        "items": list_characters(o, l),         # 실제 목록
        "offset": o,                             # 요청 오프셋
        "limit": l,                              # 요청 제한
    }

@router.get("/count", summary="캐릭터 총 개수")
def get_count():
    """등록된 캐릭터 총 수를 반환한다."""
    return {"count": count_characters()}

@router.post("", summary="캐릭터 생성")
def create_one(body: CharacterIn):
    """단일 캐릭터를 생성한다. (간단 유효성: 양끝 공백 제거)"""
    insert_character(
        body.name.strip(),
        body.summary.strip(),
        body.detail.strip(),
        body.tags,
        body.image.strip()
    )
    return {"ok": True}
