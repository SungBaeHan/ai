# Reverse Proxy (Nginx) — api.arcanaverse.ai

Oracle VM + Cloudflare Full (strict) 환경에서 80/443 수신 후 trpg-api로 프록시합니다.  
Swagger UI(`/docs`, `/redoc`, `/openapi.json`)만 외부 공개, 나머지 API는 403 차단.

## 사전 조건

- Docker, Docker Compose 설치
- Cloudflare Origin Certificate 발급 후 VM에 저장

## 실행 순서 (운영자 수행)

### 방법 A: 부트스트랩 스크립트 (권장)

```bash
cd ~/ai
chmod +x scripts/bootstrap_reverse_proxy.sh
./scripts/bootstrap_reverse_proxy.sh
# REPO_DIR 기본값: /home/ubuntu/ai (환경변수로 변경 가능)
```

위 스크립트가 app-net 생성, 인증서 디렉터리, compose 기동, reverse-proxy 기동, nginx 검증·리로드, curl 체크까지 한 번에 수행합니다.

### 방법 B: 수동

```bash
# 1) 공용 네트워크 생성 (최초 1회)
docker network create app-net || true

# 2) Cloudflare Origin Certificate를 VM에 저장
#    경로: /etc/nginx/certs/origin.pem, /etc/nginx/certs/origin.key
sudo mkdir -p /etc/nginx/certs
# (Cloudflare Dashboard → SSL/TLS → Origin Server에서 인증서 발급 후 위 경로에 저장)

# 3) 메인 앱 기동 (trpg-api, qdrant — app-net 사용)
cd ~/ai/infra
docker compose down && docker compose up -d --build

# 4) Reverse proxy 기동
docker compose -f docker-compose.reverse-proxy.yml up -d

# 5) 포트 리슨 확인
sudo ss -lntp | egrep ':80|:443'
# → reverse-proxy가 80, 443 LISTEN

# 6) 브라우저에서 확인
# https://api.arcanaverse.ai/docs
```

## 검증 커맨드

| 목적 | 커맨드 |
|------|--------|
| 포트 리슨 | `sudo ss -lntp \| egrep ':80\|:443'` → reverse-proxy가 80/443 LISTEN |
| 컨테이너·포트 | `docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"` → trpg-api는 0.0.0.0:80 없음, reverse-proxy가 80/443 |
| 내부 헬스 | `curl -i http://127.0.0.1:8000/health` |
| 외부(Cloudflare 경유) | `curl -I https://api.arcanaverse.ai/docs` |

## 파일 역할

- **docker-compose.yml** — `api`, `qdrant`가 `app-net` 사용, api는 `127.0.0.1:8000:8000`만 노출
- **docker-compose.reverse-proxy.yml** — nginx 컨테이너, 80/443 바인딩, `app-net` 연결
- **nginx/conf.d/api.arcanaverse.ai.conf** — 80→301 https, 443 SSL 종단, `/docs`·`/redoc`·`/openapi.json`만 `http://api:8000`으로 프록시

## 인증서 경로

- `/etc/nginx/certs/origin.pem` — Cloudflare Origin Certificate
- `/etc/nginx/certs/origin.key` — Private key  
(컨테이너는 해당 경로를 read-only 마운트)

## 트러블슈팅

- **523 Origin unreachable** — VM 방화벽에서 80/443 허용, reverse-proxy가 80/443 LISTEN인지 확인
- **502 Bad Gateway** — `app-net` 존재 여부, `docker compose`로 api가 기동 중인지 확인 후 `curl http://api:8000/health` (reverse-proxy 컨테이너 내부에서 테스트 시)
- **403** — 의도된 동작. `/docs`, `/redoc`, `/openapi.json`만 허용됨
