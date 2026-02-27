#!/usr/bin/env bash
set -euo pipefail

# ================================
# Bootstrap reverse-proxy for api.arcanaverse.ai
# - Creates docker network app-net
# - Ensures cert directory exists
# - Starts reverse-proxy (nginx) on 80/443
# - Reloads nginx and prints checks
# ================================

REPO_DIR="${REPO_DIR:-/home/ubuntu/ai}"
INFRA_DIR="${INFRA_DIR:-${REPO_DIR}/infra}"
REV_COMPOSE="${REV_COMPOSE:-${INFRA_DIR}/docker-compose.reverse-proxy.yml}"

CERT_DIR="/etc/nginx/certs"
CERT_PEM="${CERT_DIR}/origin.pem"
CERT_KEY="${CERT_DIR}/origin.key"

echo "===== [bootstrap_reverse_proxy] start ====="
echo "[env] REPO_DIR=${REPO_DIR}"
echo "[env] INFRA_DIR=${INFRA_DIR}"
echo "[env] REV_COMPOSE=${REV_COMPOSE}"

if [ ! -d "${INFRA_DIR}" ]; then
  echo "ERROR: INFRA_DIR not found: ${INFRA_DIR}"
  exit 1
fi

echo "[1/7] Ensure external docker network: app-net"
docker network create app-net >/dev/null 2>&1 || true
docker network ls | grep -q 'app-net' && echo "OK: app-net exists"

echo "[2/7] Ensure cert dir exists: ${CERT_DIR}"
sudo mkdir -p "${CERT_DIR}"
sudo chmod 755 "${CERT_DIR}"

echo "[3/7] Check origin cert presence"
if [ ! -f "${CERT_PEM}" ] || [ ! -f "${CERT_KEY}" ]; then
  cat <<EOF
WARN: Cloudflare Origin Certificate files not found.

You MUST place:
  - ${CERT_PEM}
  - ${CERT_KEY}

How:
  Cloudflare -> SSL/TLS -> Origin Server -> Create Certificate
  Hostname: api.arcanaverse.ai (and optionally *.arcanaverse.ai)
  Then copy cert to ${CERT_PEM} and private key to ${CERT_KEY}

For now, nginx(443) will FAIL without these files.
EOF
else
  echo "OK: cert files exist"
  sudo chmod 600 "${CERT_KEY}" || true
fi

echo "[4/7] Start app containers (api/qdrant) with compose"
cd "${INFRA_DIR}"
docker compose up -d --build

echo "[5/7] Start reverse-proxy (nginx) with 80/443"
if [ ! -f "${REV_COMPOSE}" ]; then
  echo "ERROR: reverse proxy compose not found: ${REV_COMPOSE}"
  echo "Expected file: ${INFRA_DIR}/docker-compose.reverse-proxy.yml"
  exit 1
fi

docker compose -f "${REV_COMPOSE}" up -d

echo "[6/7] Validate nginx config & reload"
if docker ps --format '{{.Names}}' | grep -q '^reverse-proxy$'; then
  docker exec reverse-proxy nginx -t
  docker exec reverse-proxy nginx -s reload || docker restart reverse-proxy
else
  echo "ERROR: reverse-proxy container not running"
  docker ps
  exit 1
fi

echo "[7/7] Checks"
echo "---- ss ports (80/443) ----"
sudo ss -lntp | egrep ':80|:443' || true

echo "---- docker ps ----"
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

echo "---- curl checks (should NOT be 523) ----"
curl -I https://api.arcanaverse.ai/docs || true
curl -I "https://api.arcanaverse.ai/v1/characters?skip=0&limit=1" || true

echo "===== [bootstrap_reverse_proxy] done ====="
