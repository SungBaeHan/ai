# 🚀 Arcanaverse API 운영 가이드

## 1️⃣ 현재 아키텍처 개요

### 🔐 네트워크 구조

```
Client (Browser)
    ↓ HTTPS
Cloudflare (Proxy ON, Full strict)
    ↓ HTTPS (Origin Certificate)
Oracle VM :443 (Nginx Reverse Proxy)
    ↓ internal Docker network (app-net)
FastAPI (trpg-api :8000)
    ↓
Qdrant (internal only)
```

---

## 2️⃣ Cloudflare 설정 기준

- **DNS**
  - api.arcanaverse.ai → A → VM Public IP
  - Proxy: ON (오렌지 구름)
- **SSL/TLS Mode**
  - Full (strict)
- **Origin Certificate 사용**
  - VM 경로:
    - /etc/nginx/certs/origin.pem
    - /etc/nginx/certs/origin.key

---

## 3️⃣ Docker 구조

### 외부 노출 포트

| 포트 | 용도 |
|------|------|
| 80   | HTTPS 리다이렉트 |
| 443  | Nginx Reverse Proxy |
| 8000 | 내부 전용 (127.0.0.1 바인딩) |

---

## 4️⃣ 배포 절차

### GitHub Action 기반 배포

```bash
scripts/deploy_from_git.sh dev
```

### 수동 배포

```bash
cd /home/ubuntu/ai
docker network create app-net || true
docker compose -f infra/docker-compose.yml up -d --build
docker compose -f infra/docker-compose.reverse-proxy.yml up -d
```

---

## 5️⃣ Reverse Proxy 재시작

```bash
docker exec reverse-proxy nginx -t
docker exec reverse-proxy nginx -s reload
```

---

## 6️⃣ 상태 점검 명령어

### 포트 확인

```bash
sudo ss -lntp | egrep ':80|:443|:8000'
```

### 컨테이너 확인

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

### API 헬스 체크

```bash
curl -i http://127.0.0.1:8000/health
```

### 외부 접근 확인

```bash
curl -I https://api.arcanaverse.ai/docs
```

---

## 7️⃣ 장애 대응 가이드

### 🔴 523 발생 시

1. 443 LISTEN 확인
2. Origin Certificate 파일 존재 확인
3. Cloudflare SSL Mode 확인 (Full strict)
4. reverse-proxy 컨테이너 상태 확인

---

### 🔴 CORS 오류 발생 시

1. nginx가 403 반환하는지 확인
2. FastAPI CORSMiddleware allow_origins 확인
3. 브라우저 preflight 요청 확인

---

### 🔴 502/Bad Gateway

1. trpg-api 컨테이너 상태 확인
2. proxy_pass 서비스명 확인
3. Docker network app-net 존재 확인

---

## 8️⃣ 신규 서브도메인 추가 절차 (예: bo.arcanaverse.ai)

1. Cloudflare DNS A 레코드 추가 (Proxy ON)
2. nginx/conf.d/bo.arcanaverse.ai.conf 생성

**템플릿:**

```nginx
server {
    listen 80;
    server_name bo.arcanaverse.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name bo.arcanaverse.ai;

    ssl_certificate /etc/nginx/certs/origin.pem;
    ssl_certificate_key /etc/nginx/certs/origin.key;

    location / {
        proxy_pass http://bo:3000;
    }
}
```

3. reverse-proxy reload

```bash
docker exec reverse-proxy nginx -t
docker exec reverse-proxy nginx -s reload
```

---

## 9️⃣ 보안 원칙

- FastAPI는 외부 직접 노출 금지
- 반드시 Reverse Proxy 경유
- 443만 외부 공개
- Docker network 내부 통신만 허용

---

## 🔟 기준 상태 정의 (Stable Baseline)

현재 운영 기준은 다음을 만족해야 한다:

- 80 → 443 리다이렉트
- 443 LISTEN
- api.arcanaverse.ai/docs 정상 응답
- trpg-api는 127.0.0.1:8000 바인딩
- Cloudflare Proxy ON + Full(strict)

---

*문서 끝*
