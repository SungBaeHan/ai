# TRPG AI 프로젝트

TRPG 캐릭터와 대화하고 질문에 답변할 수 있는 AI 애플리케이션입니다.

## 🚀 개요

이 프로젝트는 Clean Architecture 원칙을 따르는 TRPG AI 애플리케이션입니다:

- **백엔드**: FastAPI 기반 REST API 서버
- **프론트엔드**: 정적 HTML 파일 (Cloudflare Pages)
- **AI/RAG 파이프라인**: OpenAI 기반 LLM, RAG 질문 응답 시스템
- **데이터베이스**: MongoDB (프로덕션), SQLite (개발)
- **인증**: Google OAuth2 + JWT

## 🧩 설치 & 실행

### 방법 1: Docker Compose로 실행 (권장)

#### 1단계: 환경 변수 설정 (선택사항)
```bash
# 프로젝트 루트에 .env 파일 생성 (선택사항)
OLLAMA_MODEL=trpg-gen
OLLAMA_POLISH_MODEL=trpg-polish
QDRANT_URL=http://localhost:6333
COLLECTION=my_docs
```

#### 2단계: Docker Compose 실행
```bash
# 프로젝트 루트에서 실행
cd infra
docker-compose up -d

# 또는 루트에서
docker-compose -f infra/docker-compose.yml up -d
```

#### 3단계: 서비스 확인
- API 서버: http://localhost:8000
- Web UI: http://localhost:8080
- Qdrant 관리: http://localhost:6333/dashboard

#### 4단계: 서비스 중지
```bash
cd infra
docker-compose down

# 볼륨까지 삭제하려면
docker-compose down -v
```

### 방법 2: 로컬 실행

자세한 내용은 [docs/README.md](docs/README.md)를 참고하세요.

---

## 🌐 Domain Routing (MVP)

도메인별 트래픽 흐름은 다음과 같다.

| 도메인 | 경로 |
|--------|------|
| **nlp-api.arcanaverse.ai** | Cloudflare DNS(A) → VM Reverse Proxy → HF Space |

- **클라이언트** → **Cloudflare** (HTTPS) → **Oracle VM Nginx(80/443)** → **Hugging Face Space**: `https://sungbae74-traffic-accident-legal-rag.hf.space`
- **프론트엔드(Vercel)** 는 별도 배포이며, **HF Space** 는 RAG/법률 NLP API를 제공하는 백엔드 역할만 한다.

Hugging Face Spaces Free 플랜은 Custom Domain을 지원하지 않아, `nlp-api.arcanaverse.ai` 를 HF에 직접 연결하면 404가 난다. 따라서 VM에 Reverse Proxy를 두고, Nginx가 HF Space로 프록시하는 방식으로 커스텀 도메인을 제공한다.

---

## 🔁 Reverse Proxy (Nginx in Docker)

- **reverse-proxy** 컨테이너가 호스트의 **80/443** 을 점유한다.
- Nginx 설정 디렉터리:
  - **Host**: `/home/ubuntu/ai/infra/nginx/conf.d`
  - **Container**: `/etc/nginx/conf.d` (read-only 마운트)
- 인증서 디렉터리:
  - **Host**: `/etc/nginx/certs`
  - **Container**: `/etc/nginx/certs` (read-only 마운트)

`nlp-api.arcanaverse.ai` 를 HF Space로 프록시하는 설정 예시는 아래와 같다.  
업스트림이 HTTPS이므로 `proxy_set_header Host` 로 HF 호스트를 고정하고, `proxy_ssl_server_name on` 으로 SNI를 지정한다.

```nginx
server {
    listen 80;
    server_name nlp-api.arcanaverse.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nlp-api.arcanaverse.ai;

    ssl_certificate     /etc/nginx/certs/nlp-api.fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/nlp-api.privkey.pem;

    location / {
        proxy_pass https://sungbae74-traffic-accident-legal-rag.hf.space;
        proxy_set_header Host sungbae74-traffic-accident-legal-rag.hf.space;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_ssl_server_name on;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

설정 파일 경로: `infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf` (호스트 기준).

---

## 🔐 TLS (Let's Encrypt via Cloudflare DNS-01)

Cloudflare Origin Cert 대신 **Let's Encrypt** 인증서를 사용하면, curl 등 클라이언트의 issuer 검증이 통과한다. **certbot** 의 **dns-cloudflare** 플러그인으로 DNS-01 발급을 한다.

- **플러그인**: `dns-cloudflare`
- **Cloudflare API Token 권한**:
  - Zone: DNS:Edit
  - Zone: Zone:Read
  - Scope: `arcanaverse.ai`
- **Credential 파일**: `/root/.secrets/certbot/cloudflare.ini`
  - 내용 예: `dns_cloudflare_api_token = <API_TOKEN>`
  - 권한: `chmod 600`

발급 명령(한 줄):

```bash
sudo certbot certonly --dns-cloudflare --dns-cloudflare-credentials /root/.secrets/certbot/cloudflare.ini -d nlp-api.arcanaverse.ai
```

발급 후 인증서 위치:

- `/etc/letsencrypt/live/nlp-api.arcanaverse.ai/fullchain.pem`
- `/etc/letsencrypt/live/nlp-api.arcanaverse.ai/privkey.pem`

Nginx는 `/etc/nginx/certs` 를 참조하므로, 아래처럼 복사한 뒤 권한을 맞춘다.

```bash
sudo cp /etc/letsencrypt/live/nlp-api.arcanaverse.ai/fullchain.pem /etc/nginx/certs/nlp-api.fullchain.pem
sudo cp /etc/letsencrypt/live/nlp-api.arcanaverse.ai/privkey.pem   /etc/nginx/certs/nlp-api.privkey.pem
sudo chmod 644 /etc/nginx/certs/nlp-api.fullchain.pem
sudo chmod 600 /etc/nginx/certs/nlp-api.privkey.pem
```

이후 Nginx 리로드: `docker exec reverse-proxy nginx -s reload`

---

## ♻️ Certificate Sync (Renewal)

Let's Encrypt 갱신 후에도 Nginx가 쓰는 `/etc/nginx/certs` 의 복사본을 갱신해야 한다. 갱신 시마다 위의 `cp` 와 `chmod` 를 실행하고, `docker exec reverse-proxy nginx -s reload` 로 Nginx를 리로드한다.

가장 단순한 방법은 **cron** 으로 매일 새벽에 certbot 갱신 + 복사 + 리로드까지 한 번에 실행하는 것이다. 예시:

```bash
# 예: 매일 03:00에 갱신 시도 후 복사 및 nginx 리로드
0 3 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/nlp-api.arcanaverse.ai/fullchain.pem /etc/nginx/certs/nlp-api.fullchain.pem && cp /etc/letsencrypt/live/nlp-api.arcanaverse.ai/privkey.pem /etc/nginx/certs/nlp-api.privkey.pem && chmod 644 /etc/nginx/certs/nlp-api.fullchain.pem && chmod 600 /etc/nginx/certs/nlp-api.privkey.pem && docker exec reverse-proxy nginx -s reload"
```

(갱신·복사·리로드를 스크립트로 묶어서 deploy-hook에서 호출하는 방식으로 정리해 두면 유지보수가 쉽다.)  
systemd timer를 이용한 갱신/동기화는 추후로 남긴다.

---

## ✅ Verification

아래 명령으로 도메인·TLS·프록시 동작을 확인한다.

```bash
# HTTP 응답 확인 (200 기대)
curl -I https://nlp-api.arcanaverse.ai/openapi.json
curl -I https://nlp-api.arcanaverse.ai/docs

# Issuer가 Let's Encrypt 계열인지 확인
echo | openssl s_client -connect nlp-api.arcanaverse.ai:443 -servername nlp-api.arcanaverse.ai 2>/dev/null | openssl x509 -noout -issuer
```

- **기대 결과**: HTTP 200, Issuer에 `Let's Encrypt` 포함.

---

## 📅 작업 로그 (요약)

> 상세한 일자별 작업 내역은 `docs/logs/` 아래 md 파일들에 기록한다.
> README에는 최근 작업 몇 개만 요약해서 보여준다.

### 2025-12

- 12/04: World API 구현 (GET /v1/worlds 목록 조회, GET /v1/worlds/{id} 상세 조회)
- 12/04: World 이미지 경로 정규화 (R2 public URL로 자동 변환)
- 12/04: World 상세 페이지 구현 (world.html, 인사말 없이 자유롭게 채팅 시작)
- 12/03: 암호화된 user_info_v2 토큰 시스템 구현 (Fernet 암호화, 세션 검증 API, 세션 만료 처리)
- 12/03: 세션 검증 응답에 email 필드 추가, 프론트엔드 세션 관리 개선

### 2025-01

- 01/27: 사용자 인증 및 계정 관리 시스템 구축 (User CRUD API, MongoDB 연동, 계정 상태 관리)
- 01/27: Google OAuth 인증 개선 (MongoDB users 컬렉션 자동 연동, is_use/is_lock 플래그 반환)
- 01/27: 프론트엔드 계정 상태 관리 (my.html, chat.html 수정, localStorage 버전 관리)

### 2025-11

- 11/25: LLM 엔진을 OpenAI로 강제 통일 (gpt-4o-mini, max_tokens=32)
- 11/24: 프론트엔드 API 경로에서 `/api` prefix 제거, nginx 프록시 제거
- 11/21: LLM Provider를 OpenAI로 전환 (환경변수 기반 선택)
- 11/19: 프론트 API 베이스 URL 정리, R2 Public URL 빌더 함수 생성
- 11/07: MongoDB 어댑터 및 마이그레이션 시스템 구축, Cloudflare R2 스토리지 통합
- 11/05: Cloudflare 설정, Render 배포 설정

👉 **전체 상세 로그:** [docs/logs](docs/logs)

## 📂 문서 구조

- `docs/logs/` : 일자별/월별 작업 로그 (가장 자세한 내용)
- `docs/architecture/` : 아키텍처, 구성도, 설계 문서
- `docs/infra/` : Oracle VM, Docker, 배포 관련 인프라 문서
- `docs/misc/` : 위에 분류하기 애매한 문서들 (임시)

## 📌 TODO / 향후 계획

- [ ] 사용자 관리 기능 강화 (관리자 페이지)
- [ ] API 성능 모니터링 및 최적화
- [ ] 테스트 코드 작성 (단위 테스트, 통합 테스트)
- [ ] 구조화된 로깅 (JSON 형태) 도입

## API 엔드포인트

### 캐릭터 API
- `GET /v1/characters` - 캐릭터 목록
- `GET /v1/characters/{id}` - 캐릭터 상세
- `GET /v1/characters/count` - 캐릭터 개수
- `POST /v1/characters` - 캐릭터 생성

### 세계관 API
- `GET /v1/worlds` - 세계관 목록
- `GET /v1/worlds/{id}` - 세계관 상세

### 채팅 API
- `POST /v1/chat/` - TRPG 채팅
- `POST /v1/chat/reset` - 세션 리셋

### 질의응답 API
- `GET /v1/ask?q={질문}` - RAG 기반 질문 응답
- `GET /v1/ask/health` - 건강 상태 확인

### 인증 API
- `POST /v1/auth/google` - 구글 로그인
- `POST /v1/auth/validate-session` - 세션 검증 (user_info_v2 토큰 검증)
- `GET /v1/auth/me` - 현재 사용자 정보 조회
- `POST /v1/auth/logout` - 로그아웃

### 사용자 관리 API
- `POST /v1/users` - 사용자 생성
- `GET /v1/users/{user_id}` - 사용자 조회
- `PATCH /v1/users/{user_id}` - 사용자 수정
- `DELETE /v1/users/{user_id}` - 사용자 삭제

### 헬스 체크
- `GET /health` - 전체 서비스 건강 상태
- `GET /health/env` - 환경변수 확인
- `GET /health/db` - 데이터베이스 연결 상태

## 프로젝트 구조 상세

### Domain Layer (`src/domain/`)
- 도메인 엔티티 정의 (Character 등)

### Use Cases Layer (`src/usecases/`)
- 비즈니스 로직 (GetCharacter, ListCharacters, AnswerQuestion 등)

### Ports Layer (`src/ports/`)
- 인터페이스 정의 (Repository, Service 등)

### Adapters Layer (`adapters/`)
- 인프라 구현체 (SQLite, MongoDB, OpenAI, R2 등)

자세한 구조는 [docs/architecture/](docs/architecture/)를 참고하세요.

## 라이선스

(라이선스 정보 추가)
