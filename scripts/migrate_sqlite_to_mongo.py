"""
Usage:

  # (Windows 예시)

  set MONGO_URI=mongodb+srv://<USER>:<PASS>@<cluster>.mongodb.net/

  set MONGO_DB=arcanaverse

  python scripts/migrate_sqlite_to_mongo.py --sqlite ".\\data\\db\\app.sqlite3" --tables characters --limit 5000



  # (WSL/리눅스 예시)

  export MONGO_URI="mongodb+srv://<USER>:<PASS>@<cluster>.mongodb.net/"

  export MONGO_DB="arcanaverse"

  python scripts/migrate_sqlite_to_mongo.py --sqlite "./data/db/app.sqlite3" --tables characters --limit 5000

"""

import os, sqlite3, json, argparse

from pymongo import MongoClient


def read_rows(sqlite_path: str, table: str, limit: int):
    con = sqlite3.connect(sqlite_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
        for row in cur.fetchall():
            d = dict(row)
            # bytes -> str
            for k, v in list(d.items()):
                if isinstance(v, (bytes, bytearray)):
                    d[k] = v.decode("utf-8", errors="ignore")
            d.pop("_id", None)
            yield d
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", required=True, help="Path to local SQLite file")
    ap.add_argument("--tables", default="characters", help="Comma-separated table names")
    ap.add_argument("--limit", type=int, default=10000)
    args = ap.parse_args()

    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "arcanaverse")
    if not uri:
        raise SystemExit("ERROR: MONGO_URI env not set")

    client = MongoClient(uri, appname="arcanaverse-local-migrator")
    mdb = client[db_name]

    moved = {}
    for t in [s.strip() for s in args.tables.split(",") if s.strip()]:
        col = mdb[t]
        count = 0
        for doc in read_rows(args.sqlite, t, args.limit):
            # upsert key 우선순위: id > key > 임시 키
            key = {}
            if "id" in doc: key = {"id": doc["id"]}
            elif "key" in doc: key = {"key": doc["key"]}
            col.update_one(key if key else {"_temp_pk": json.dumps(doc, sort_keys=True)[:128]},
                           {"$set": doc}, upsert=True)
            count += 1
        moved[t] = count

    print({"ok": True, "moved": moved, "db": db_name})


if __name__ == "__main__":
    main()

