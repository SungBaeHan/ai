#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-dev}"

PROJECT_ROOT="/home/ubuntu/ai"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "===== [deploy_from_git] branch: ${BRANCH} ====="

cd "$PROJECT_ROOT"

echo "[git] fetch & checkout ${BRANCH}"
git fetch origin
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

echo "[deploy] move to infra dir: ${INFRA_DIR}"
cd "$INFRA_DIR"

echo "[docker] compose down"
docker compose down

echo "[docker] compose pull"
docker compose pull

echo "[docker] compose up -d"
docker compose up -d

echo "===== [deploy_from_git] done ====="