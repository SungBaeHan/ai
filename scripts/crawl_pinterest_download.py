#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
[1/2] Pinterest 이미지 다운로드 전용
- Pinterest 검색 URL에서 1~10개의 이미지 원본을 수집하고 temp 폴더에만 저장.
- 파일명은 URL에서 유추한 원본명 사용. 같은 이름이 있으면 _1, _2 ... 자동 부여.
- DB, LLM, 메타 생성은 하지 않음.

예)
python crawl_pinterest_download.py \
  --url "https://kr.pinterest.com/search/pins/?q=캐릭터%20일러스트%20여자%20전신%20그림" \
  --count 6 \
  --temp-dir "F:/git/ai/apps/web-html/assets/temp"
"""

import argparse
import os
import re
import time
from pathlib import Path
from typing import List
import requests
from bs4 import BeautifulSoup

def collect_image_urls_with_playwright(url: str, need: int) -> List[str]:
    from playwright.sync_api import sync_playwright
    urls, seen = [], set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
        )
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)

        for _ in range(20):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            for img in soup.select('img[src^="https://i.pinimg.com/"]'):
                src = img.get("src") or ""
                if not src:
                    continue
                high = re.sub(r"/\d+x/", "/originals/", src)
                cand = high if "originals" in high else src
                if cand not in seen:
                    seen.add(cand)
                    urls.append(cand)
                    if len(urls) >= need:
                        break
            if len(urls) >= need:
                break

        browser.close()
    return urls[:need]

def infer_filename_from_url(u: str) -> str:
    # URL의 마지막 세그먼트를 파일명으로 사용, 확장자 없으면 .jpg
    name = u.split("?")[0].rstrip("/").split("/")[-1]
    if not re.search(r"\.(jpg|jpeg|png|webp)$", name, re.IGNORECASE):
        name += ".jpg"
    return name

def ensure_unique_path(base_dir: Path, filename: str) -> Path:
    cand = base_dir / filename
    if not cand.exists():
        return cand
    stem = cand.stem
    suffix = cand.suffix
    i = 1
    while True:
        c = base_dir / f"{stem}_{i}{suffix}"
        if not c.exists():
            return c
        i += 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Pinterest 검색 URL")
    ap.add_argument("--count", type=int, default=5, help="다운로드 개수 (1~10)")
    ap.add_argument("--temp-dir", default="./apps/web-html/assets/temp", help="임시 저장 디렉토리")
    args = ap.parse_args()

    if args.count < 1 or args.count > 10:
        raise SystemExit("count는 1~10 사이여야 합니다.")

    temp_dir = Path(args.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("[DL] Pinterest 이미지 URL 수집…")
    urls = collect_image_urls_with_playwright(args.url, args.count)
    if not urls:
        print("  → 수집 실패(0건)")
        return
    print(f"  → 후보 {len(urls)}개")

    saved = 0
    for i, u in enumerate(urls, 1):
        try:
            r = requests.get(u, timeout=25, headers={"Referer": "https://www.pinterest.com/"})
            r.raise_for_status()
            fname = infer_filename_from_url(u)
            out_path = ensure_unique_path(temp_dir, fname)
            out_path.write_bytes(r.content)
            print(f" + {i}/{len(urls)} 저장: {out_path.name}")
            saved += 1
            time.sleep(0.2)
        except Exception as e:
            print(f" ! {i}/{len(urls)} 실패: {e}")

    print(f"[DL] 완료: 저장 {saved} / 요청 {len(urls)}")

if __name__ == "__main__":
    main()
