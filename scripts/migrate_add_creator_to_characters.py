"""
MongoDB characters 컬렉션에 creator 필드 추가 마이그레이션

Usage:
  # 환경변수 설정
  set MONGO_URI=mongodb+srv://<USER>:<PASS>@<cluster>.mongodb.net/
  set MONGO_DB_NAME=arcanaverse

  # 실행
  python scripts/migrate_add_creator_to_characters.py
"""

import os
from pymongo import MongoClient
import certifi

def main():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB", "arcanaverse")
    
    if not uri:
        raise SystemExit("ERROR: MONGO_URI env not set")
    
    if not uri.startswith("mongodb+srv://"):
        raise SystemExit("ERROR: MONGO_URI must use 'mongodb+srv://'")
    
    # MongoDB 연결
    client = MongoClient(
        uri,
        appname="arcanaverse-creator-migration",
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=20000,
        socketTimeoutMS=20000,
    )
    db = client[db_name]
    collection = db["characters"]
    
    # creator 필드가 없는 문서들에 creator: null 추가
    result = collection.update_many(
        {"creator": {"$exists": False}},
        {"$set": {"creator": None}}
    )
    
    print(f"Migration completed:")
    print(f"  - Documents updated: {result.modified_count}")
    print(f"  - Total documents matched: {result.matched_count}")
    print(f"  - Database: {db_name}")
    print(f"  - Collection: characters")
    
    # 검증: creator 필드가 없는 문서가 남아있는지 확인
    remaining = collection.count_documents({"creator": {"$exists": False}})
    if remaining > 0:
        print(f"  WARNING: {remaining} documents still missing creator field")
    else:
        print(f"  ✓ All documents now have creator field")

if __name__ == "__main__":
    main()

