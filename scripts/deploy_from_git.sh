#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-dev}"

echo "===== [deploy_from_git] branch: ${BRANCH} ====="

REPO_DIR="/home/ubuntu/ai"
INFRA_DIR="${REPO_DIR}/infra"
REV_PROXY_COMPOSE="${INFRA_DIR}/docker-compose.reverse-proxy.yml"
CERT_DIR="/etc/nginx/certs"
CERT_PEM="${CERT_DIR}/origin.pem"
CERT_KEY="${CERT_DIR}/origin.key"

cd "${REPO_DIR}"

echo "[git] fetch & hard reset to origin/${BRANCH}"

git fetch origin "${BRANCH}"

if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
  git checkout "${BRANCH}"
else
  git checkout -b "${BRANCH}" "origin/${BRANCH}"
fi

git reset --hard "origin/${BRANCH}"

echo "[docker] ensure external network: app-net"
docker network create app-net >/dev/null 2>&1 || true

echo "[docker] docker compose pull & up (app containers)"
cd "${INFRA_DIR}"

docker compose pull
docker compose up -d --build

# reverse-proxy compose 파일이 있을 때만 올림
if [ -f "${REV_PROXY_COMPOSE}" ]; then
  echo "[reverse-proxy] cert check (Cloudflare Origin Cert)"
  if [ ! -f "${CERT_PEM}" ] || [ ! -f "${CERT_KEY}" ]; then
    echo "WARN: origin cert not found:"
    echo "  - ${CERT_PEM}"
    echo "  - ${CERT_KEY}"
    echo "Cloudflare -> SSL/TLS -> Origin Server에서 발급 후 위 경로에 저장하세요."
  fi

  echo "[reverse-proxy] up -d"
  docker compose -f "${REV_PROXY_COMPOSE}" up -d

  echo "[reverse-proxy] nginx config test"
  docker exec reverse-proxy nginx -t

  echo "[reverse-proxy] reload"
  docker exec reverse-proxy nginx -s reload || docker restart reverse-proxy
else
  echo "INFO: ${REV_PROXY_COMPOSE} not found. skip reverse-proxy."
fi

echo "===== [deploy_from_git] done ====="