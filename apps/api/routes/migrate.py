# apps/api/routes/migrate.py
"""
SQLite → MongoDB 마이그레이션 라우트
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import os
import sqlite3
from adapters.persistence.sqlite import get_conn
from adapters.persistence.mongo import get_db, init_db
from adapters.persistence.mongo.factory import create_character_repository
from src.domain.character import Character

router = APIRouter(prefix="/_ops/migrate", tags=["migrate"])


def migrate_table_sqlite_to_mongo(table_name: str, limit: int = 5000) -> dict:
    """SQLite 테이블을 MongoDB로 마이그레이션"""
    if table_name != "characters":
        raise HTTPException(status_code=400, detail=f"Unsupported table: {table_name}")
    
    # MongoDB 초기화
    init_db()
    mongo_repo = create_character_repository()
    mongo_collection = get_db().characters
    
    # SQLite에서 데이터 읽기
    db_path = os.getenv("DB_PATH", "/data/db/app.sqlite3")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # SQLite에서 모든 레코드 조회
        cursor = conn.execute("""
            SELECT id, name, summary, detail, tags, image, created_at,
                   archetype, background, scenario, system_prompt, greeting,
                   world, genre, style, img_hash, src_file
            FROM characters
            ORDER BY id
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        migrated = 0
        skipped = 0
        errors = []
        
        for row in rows:
            try:
                # SQLite row를 dict로 변환
                data = dict(row)
                
                # tags를 파싱 (JSON 문자열일 수 있음)
                import json
                tags = data.get("tags", "[]")
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                data["tags"] = tags if isinstance(tags, list) else []
                
                # Character 엔티티 생성
                character = Character.from_dict(data)
                
                # MongoDB에 upsert (image 기준)
                mongo_repo.upsert_by_image(character)
                migrated += 1
            except Exception as e:
                skipped += 1
                errors.append(f"Row id={row.get('id')}: {str(e)}")
        
        return {
            "table": table_name,
            "total_read": len(rows),
            "migrated": migrated,
            "skipped": skipped,
            "errors": errors[:10] if errors else []  # 최대 10개 에러만
        }
    finally:
        conn.close()


@router.post("/sqlite-to-mongo")
def migrate_sqlite_to_mongo(
    tables: str = Query(..., description="마이그레이션할 테이블 목록 (쉼표 구분)"),
    limit: int = Query(5000, ge=1, le=100000, description="최대 레코드 수")
):
    """SQLite에서 MongoDB로 데이터 마이그레이션"""
    table_list = [t.strip() for t in tables.split(",")]
    results = {}
    
    for table in table_list:
        try:
            results[table] = migrate_table_sqlite_to_mongo(table, limit)
        except Exception as e:
            results[table] = {"error": str(e)}
    
    return {
        "status": "completed",
        "results": results
    }

