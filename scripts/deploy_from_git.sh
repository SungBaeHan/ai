#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-dev}"

echo "===== [deploy_from_git] branch: ${BRANCH} ====="

cd /home/ubuntu/ai

echo "[git] fetch & hard reset to origin/${BRANCH}"

# 원격 최신 가져오기
git fetch origin "${BRANCH}"

# 브랜치 체크아웃 (없으면 생성)
if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
  git checkout "${BRANCH}"
else
  git checkout -b "${BRANCH}" "origin/${BRANCH}"
fi

# 로컬 변경사항 전부 버리고 원격 상태로 맞추기
git reset --hard "origin/${BRANCH}"

echo "[docker] docker compose pull & up"

cd infra

# 필요하면 이미지 pull
docker compose pull

# 컨테이너 재시작 (없으면 새로 생성)
docker compose up -d --build

echo "===== [deploy_from_git] done ====="
