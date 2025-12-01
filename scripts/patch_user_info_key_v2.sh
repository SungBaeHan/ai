#!/usr/bin/env bash

set -e

cd "$(git rev-parse --show-toplevel)"

# 1) my.html, chat.html 에서 USER_INFO_KEY 값 변경

python - << 'PY'

from pathlib import Path

targets = [
    Path("apps/web-html/my.html"),
    Path("apps/web-html/chat.html"),
]

for path in targets:
    if not path.exists():
        print("skip (no file):", path)
        continue
    
    text = path.read_text(encoding="utf-8")
    if "USER_INFO_KEY" not in text:
        print("skip (no USER_INFO_KEY):", path)
        continue
    
    new = text.replace("const USER_INFO_KEY = 'user_info';",
                       "const USER_INFO_KEY = 'user_info_v2';")
    path.write_text(new, encoding="utf-8")
    print("patched:", path)

PY

