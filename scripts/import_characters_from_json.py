# scripts/import_characters_from_json.py
import json, os
from pathlib import Path
from packages.db import init_db, insert_character

ROOT = Path(__file__).resolve().parents[1]
# /json은 web 쪽이 우선 mount 되므로 여길 1순위로
CANDIDATES = [
    ROOT / "apps" / "web-html" / "json" / "characters.json",
    ROOT / "data" / "json" / "characters.json",
]

def load_json():
    for p in CANDIDATES:
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("characters.json not found in web-html/json or data/json")

def main():
    data = load_json()
    items = data.get("characters", [])
    init_db()
    for c in items:
        name     = c.get("name", "이름없음")
        summary  = c.get("shortBio", "").strip() or "간단 소개가 없습니다."
        detail   = c.get("longBio", "").strip()
        tags     = c.get("tags", ["TRPG","캐릭터"])
        image    = c.get("image") or f"/assets/char/{c.get('id','char_xx')}.jpg"
        insert_character(name, summary, detail, tags, image)
    print(f"OK: inserted {len(items)} characters")

if __name__ == "__main__":
    main()
