#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$HOME/ai}"
INFRA_DIR="$ROOT/infra"
COMPOSE_FILE="$INFRA_DIR/docker-compose.yml"

echo ">>> [1/5] docker-compose.yml 백업"
cp -a "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%Y%m%d%H%M%S)"

echo ">>> [2/5] qdrant healthcheck 를 /readyz + start_period 로 교체"
# compose 전체를 읽어 healthcheck 블록만 안전하게 치환
tmp="${COMPOSE_FILE}.tmp.$$"
awk '
  BEGIN{in_q=0; in_h=0}
  # qdrant 서비스 시작 감지
  /^[[:space:]]*qdrant:/ && prev!~/services:/ { in_q=1 }
  # 다른 서비스로 넘어가면 qdrant 영역 종료
  in_q && /^[^[:space:]]/ && $0 !~ /^services:/ && $0 !~ /^[[:space:]]*qdrant:/ { in_q=0 }
  { prev=$0 }

  # qdrant 블록 안에서 healthcheck 시작/끝 감지
  in_q && /^[[:space:]]*healthcheck:/ { in_h=1; next }
  in_h && /^[[:space:]]{2}[^[:space:]]/ { in_h=0 }  # 들여쓰기 2스페이스로 새로운 키 시작이면 healthcheck 종료

  # healthcheck 본문은 버리고, qdrant 블록의 적당한 위치에 새 블록 삽입을 위해 저장
  {
    if (!in_h) print $0
    if (in_q && $0 ~ /^[[:space:]]*volumes:/) {
      print "    healthcheck:"
      print "      test: [\"CMD\", \"curl\", \"-sf\", \"http://127.0.0.1:6333/readyz\"]"
      print "      interval: 5s"
      print "      timeout: 3s"
      print "      retries: 25"
      print "      start_period: 25s"
    }
  }
' "$COMPOSE_FILE" > "$tmp"

mv "$tmp" "$COMPOSE_FILE"

echo ">>> [3/5] 재배포"
cd "$INFRA_DIR"
docker compose down
docker compose up -d --build

echo ">>> [4/5] qdrant 기동/헬스 확인 (약간 대기)"
sleep 5
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo "Health: qdrant => $(docker inspect -f '{{.State.Health.Status}}' qdrant 2>/dev/null || echo 'no-healthcheck')"

# 컨테이너 내부에서 직접 readyz 체크 (curl 존재 및 엔드포인트 확인)
echo ">>> [5/5] 컨테이너 내부 readyz 점검"
docker exec qdrant sh -lc 'curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:6333/readyz' || true
echo "Done."
