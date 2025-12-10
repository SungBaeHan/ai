#!/usr/bin/env bash

set -euo pipefail

# 레포 루트로 이동
cd "$(git rev-parse --show-toplevel)"

echo "[1] requirements.txt 에서 playwright 제거..."

python - << 'PY'
from pathlib import Path

req_path = Path("requirements.txt")
text = req_path.read_text(encoding="utf-8").splitlines()

out_lines = []
for line in text:
    # 공백 제거 후 playwright 라인만 스킵
    if line.strip().startswith("playwright"):
        continue
    out_lines.append(line)

req_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print("[OK] playwright 줄 제거 완료")
PY

echo "[2] docker/api.Dockerfile 에서 build-essential 제거..."

python - << 'PY'
from pathlib import Path

docker_path = Path("docker/api.Dockerfile")
text = docker_path.read_text(encoding="utf-8")

old = """RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential curl && \\
    rm -rf /var/lib/apt/lists/*"""
new = """RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl && \\
    rm -rf /var/lib/apt/lists/*"""

if old not in text:
    raise SystemExit("[ERROR] 예상했던 apt-get 블록을 docker/api.Dockerfile 에서 찾지 못했습니다. 수동으로 확인해주세요.")

docker_path.write_text(text.replace(old, new), encoding="utf-8")
print("[OK] build-essential 제거 완료 (curl만 설치)")

PY

echo
echo "=== 변경 완료 ==="
echo "변경 내용 확인 후, 아래처럼 다시 빌드/배포하세요:"
echo "  cd infra"
echo "  docker compose build api"
echo "  docker compose up -d api"

