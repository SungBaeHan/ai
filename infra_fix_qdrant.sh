#!/usr/bin/env bash

set -euo pipefail

ROOT="${ROOT:-$HOME/ai}"
INFRA_DIR="$ROOT/infra"
DOCKER_DIR="$ROOT/docker"
VOL_DIR="$ROOT/_volumes/qdrant_storage"
ENV_FILE="$ROOT/.env"
COMPOSE_FILE="$INFRA_DIR/docker-compose.yml"
QDRANT_DOCKERFILE="$DOCKER_DIR/qdrant.Dockerfile"

echo ">>> [1/7] 디렉터리 준비"
mkdir -p "$DOCKER_DIR" "$INFRA_DIR" "$VOL_DIR"

echo ">>> [2/7] qdrant Dockerfile(curl 포함) 생성: $QDRANT_DOCKERFILE"
cat > "$QDRANT_DOCKERFILE" <<'DOCKERFILE'
FROM qdrant/qdrant:latest
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
USER 1000
DOCKERFILE

echo ">>> [3/7] .env 확인/보정: $ENV_FILE"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'ENVVARS'
APP_ENV=prod
PORT=8000
APP_MODULE=apps.api.main:app
UVICORN_WORKERS=2
PYTHONUNBUFFERED=1

QDRANT_URL=http://qdrant:6333
COLLECTION=my_docs

OLLAMA_MODEL=trpg-gen:latest
OLLAMA_POLISH_MODEL=trpg-polish:latest

GOOGLE_CLIENT_ID=__FILL_ME__
GOOGLE_CLIENT_SECRET=__FILL_ME__
JWT_SECRET=__CHANGE_ME_STRONG__

CORS_ALLOW_ORIGINS=http://localhost:8080,https://arcanaverse.ai,https://www.arcanaverse.ai
ENVVARS
  echo "    - 새 .env 생성"
else
  # PORT=8000 강제 보정(없거나 다른 값이면 8000으로)
  if ! grep -q '^PORT=' "$ENV_FILE"; then
    echo "PORT=8000" >> "$ENV_FILE"
    echo "    - .env에 PORT=8000 추가"
  else
    sed -i 's/^PORT=.*/PORT=8000/' "$ENV_FILE"
    echo "    - .env PORT=8000으로 보정"
  fi
fi

echo ">>> [4/7] docker-compose.yml 백업 및 갱신: $COMPOSE_FILE"
if [ -f "$COMPOSE_FILE" ]; then
  cp -a "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%Y%m%d%H%M%S)"
fi

# 최신 compose 내용으로 교체(헬스체크 정상 동작 버전)
cat > "$COMPOSE_FILE" <<'YAML'
services:

  qdrant:
    build:
      context: ..                    # ~/ai
      dockerfile: docker/qdrant.Dockerfile
    image: local/qdrant-with-curl:latest
    container_name: qdrant
    restart: unless-stopped
    ports:
      - 127.0.0.1:6333:6333
      - 127.0.0.1:6334:6334
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    volumes:
      - ../_volumes/qdrant_storage:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://127.0.0.1:6333/healthz"]
      interval: 5s
      timeout: 2s
      retries: 20

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ../_volumes/ollama_models:/root/.ollama
    entrypoint: ["/bin/sh", "-lc", "ollama serve"]

  api:
    build:
      context: ..                   # repo 루트(~/ai)
      dockerfile: docker/api.Dockerfile
    container_name: trpg-api
    restart: unless-stopped
    depends_on:
      qdrant:
        condition: service_healthy
      # ollama:
      #   condition: service_started
    env_file:
      - ../.env
    environment:
      QDRANT_URL: "http://qdrant:6333"
    ports:
      - "8000:8000"
    volumes:
      - ../apps:/app/apps:ro
      - ../packages:/app/packages:ro
      - ../adapters:/app/adapters:ro
      - ../src:/app/src:ro
      - ../assets:/app/assets:ro
      - ../data/json:/app/data/json:ro
    entrypoint: ["/app/infra/docker-entrypoint.sh"]
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://127.0.0.1:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 20

  web:
    build:
      context: ..                   # repo 루트(~/ai)
      dockerfile: docker/nginx.Dockerfile
    container_name: trpg-web
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    ports:
      - "8080:80"
    volumes:
      - ../apps/web-html:/usr/share/nginx/html
      - ../assets:/usr/share/nginx/html/assets:ro

volumes:
  qdrant_storage:
    driver: local
  ollama_models:
    driver: local
YAML

echo ">>> [5/7] qdrant 볼륨 권한 보정: $VOL_DIR (uid:1000)"
sudo chown -R 1000:1000 "$VOL_DIR" || true
sudo chmod -R 775 "$VOL_DIR" || true

echo ">>> [6/7] 컨테이너 재배포"
cd "$INFRA_DIR"
docker compose down
docker compose up -d --build

echo ">>> [7/7] 상태 확인"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo
echo "Health: qdrant => $(docker inspect -f '{{.State.Health.Status}}' qdrant 2>/dev/null || echo 'no-healthcheck')"
echo "Health: trpg-api => $(docker inspect -f '{{.State.Health.Status}}' trpg-api 2>/dev/null || echo 'no-healthcheck')"

echo
echo "Try:"
echo "  - curl -sS http://127.0.0.1:6333/healthz && echo ' <- qdrant OK'"
echo "  - curl -sS http://127.0.0.1:8000/health && echo ' <- api OK'"
echo
echo "Open:"
echo "  - API Swagger:  http://<SERVER_IP>:8000/docs"
echo "  - Web Static:   http://<SERVER_IP>:8080"

