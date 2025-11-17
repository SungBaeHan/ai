# adapters/persistence/sqlite/character_repository_adapter.py
"""
SQLite CharacterRepository 어댑터
기존 adapters.persistence.sqlite 함수들을 래핑하여 포트 인터페이스 구현

[몽고 전환 후 legacy]
SQLite는 이제 선택적 백엔드입니다. DB_BACKEND=sqlite일 때만 사용됩니다.
"""

from typing import List, Optional
from src.domain.character import Character
from src.ports.repositories.character_repository import CharacterRepository
from adapters.persistence.sqlite import (
    get_character_by_id as get_by_id_raw,
    list_characters as list_all_raw,
    count_characters as count_raw,
    insert_character as create_raw,
    upsert_character_by_image as upsert_by_image_raw,
    init_db,
)


class SQLiteCharacterRepository(CharacterRepository):
    """SQLite 구현체 (레거시 지원용)"""
    
    def __init__(self):
        """SQLite Repository 초기화 - 필요시 DB 초기화"""
        # SQLite 사용 시에만 초기화 (한 번만 실행)
        try:
            init_db()
        except Exception as e:
            # 초기화 실패해도 계속 진행 (이미 테이블이 있을 수 있음)
            print(f"[WARN] SQLite init_db failed (may already exist): {e}")
    
    def get_by_id(self, char_id: int) -> Optional[Character]:
        """ID로 캐릭터 조회"""
        data = get_by_id_raw(char_id)
        if not data:
            return None
        return Character.from_dict(data)
    
    def list_all(self, offset: int = 0, limit: int = 30) -> List[Character]:
        """캐릭터 목록 조회"""
        data_list = list_all_raw(offset=offset, limit=limit)
        return [Character.from_dict(data) for data in data_list]
    
    def count(self) -> int:
        """캐릭터 총 개수 조회"""
        return count_raw()
    
    def create(self, character: Character) -> Character:
        """새 캐릭터 생성"""
        create_raw(
            name=character.name,
            summary=character.summary,
            detail=character.detail,
            tags=character.tags,
            image=character.image
        )
        # 생성 후 조회 (ID를 얻기 위해)
        # 실제 구현에서는 insert 후 ID를 반환하도록 수정 필요
        return character
    
    def upsert_by_image(self, character: Character) -> Character:
        """이미지 경로로 캐릭터 upsert"""
        upsert_by_image_raw(
            name=character.name,
            summary=character.summary,
            detail=character.detail,
            tags=character.tags,
            image=character.image,
            archetype=character.archetype,
            background=character.background,
            scenario=character.scenario,
            system_prompt=character.system_prompt,
            greeting=character.greeting,
            world=character.world,
            genre=character.genre,
            style=character.style,
        )
        return character
