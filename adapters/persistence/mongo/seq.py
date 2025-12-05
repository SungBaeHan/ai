# adapters/persistence/mongo/seq.py
"""
MongoDB 시퀀스 카운터 유틸리티
"""

from adapters.persistence.mongo import get_db


async def get_next_sequence(collection_name: str) -> int:
    """
    MongoDB 시퀀스 컬렉션을 사용하여 다음 시퀀스 번호를 반환합니다.
    
    Args:
        collection_name: 시퀀스를 가져올 컬렉션 이름 (예: "characters")
    
    Returns:
        다음 시퀀스 번호
    """
    db = get_db()
    seq_collection = db["sequences"]
    
    result = seq_collection.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    return result["seq"]

