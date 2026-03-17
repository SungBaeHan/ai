# SSOT — Single Source of Truth (Repository)

> 이 문서는 이 저장소의 **단일 진실 소스(SSOT)** 이다.  
> 사람/AI(Codex/Cursor/Atlas)는 레포 작업 시 **반드시 이 문서 기준으로만** 파일을 생성·수정·커밋한다.
>
> 루트 `README.md` 및 `docs/README.md`, `docs/QUICK_START.md`는 **요약/가이드**이며, 충돌 시 **본 SSOT가 우선**한다.

---

## 1. 레포 스코프 (이 레포에 존재하는 구성요소)

이 저장소는 다음 구성요소를 포함한다.

- **Backend API**: `apps/api/` (FastAPI)
- **정적 HTML 프론트**: `apps/web-html/`
- **어댑터 계층**: `adapters/` (외부 연동, 스토리지, 영속성)
- **도메인/포트/유스케이스**: `src/`
- **인프라/컨테이너**: `docker/`, `infra/docker-compose.yml`, 루트 `Dockerfile`, `render.yaml`
- **문서**: `docs/` (architecture/infra/logs/misc/scratch)
- **운영/유틸 스크립트**: `scripts/`
- **데이터 스냅샷**: `data/`
- **React(TSX) 소스**: `html/app/web/src/` (배포/연결 기준은 미정 항목 참고)
- **테스트**: `tests/`

---

## 2. 최우선 엔트리포인트/연결 기준

### 2.1 API (FastAPI)

- 엔트리포인트: `apps/api/main.py`
- 부트스트랩/설정: `apps/api/bootstrap.py`, `apps/api/config.py`, `apps/api/startup.py`
- 라우팅: `apps/api/routes/`
- 헬스체크 기준:
  - `render.yaml`이 `healthCheckPath: /health` 사용

### 2.2 정적 HTML 프론트

- 위치: `apps/web-html/`
- 구조:
  - `index.html` (home.html 리다이렉트)
  - `home.html`, `chat.html`, `game.html`, `search.html`, `world.html`, `my.html`, `personas.html`
  - `create/` 하위 생성 화면
  - `js/` 및 `static/js/` 존재

### 2.3 데이터/정적 리소스

- 데이터 JSON: `data/json/` (예: `characters.json`, `home.json`)
- API에서 참조 경로:
  - `apps/api/main.py` 기준 `JSON_DIR = ROOT / "data" / "json"`
  - `ASSETS_DIR` 등 정적 파일 참조는 API에서 수행

### 2.4 어댑터/영속성

- 외부/LLM/임베딩: `adapters/external/`
- 스토리지(R2): `adapters/file_storage/r2_storage.py`
- 영속성:
  - Mongo: `adapters/persistence/mongo/`
  - SQLite: `adapters/persistence/sqlite/`
  - 선택/생성: `adapters/persistence/factory.py`

### 2.5 컨테이너/배포

- 로컬/서비스 구성:
  - `infra/docker-compose.yml` (qdrant, api 서비스 정의)
- Docker 빌드 파일:
  - `docker/api.Dockerfile`, `docker/nginx.Dockerfile`, `docker/nginx.conf`
  - 루트 `Dockerfile` (Render 등에서 사용)
- Render:
  - `render.yaml`이 루트 `Dockerfile`을 참조

---

## 3. 디렉터리 책임(역할) 요약

| 경로 | 책임/역할 | 비고 |
|---|---|---|
| `apps/api/` | FastAPI 백엔드 | main/bootstrap/startup/routes |
| `apps/web-html/` | 정적 HTML 프론트 | js/static/js 포함 |
| `apps/llm/prompts/` | LLM 프롬프트 정의 | `trpg_game_master.py` |
| `adapters/` | 외부/스토리지/DB 어댑터 | persistence mongo/sqlite |
| `src/` | domain/ports/usecases | 클린 아키텍처 성격 |
| `infra/` | docker-compose 및 엔트리포인트 스크립트 | qdrant/api 연동 |
| `docker/` | dockerfile, nginx 구성 | compose에서 참조 |
| `docs/` | 문서 허브 | architecture/infra/logs/misc/scratch |
| `scripts/` | 운영/유틸/마이그레이션 스크립트 | `migrate_*.py` 등 |
| `data/` | 정적 데이터 | `data/json/` |
| `html/app/web/src/` | React(TSX) 소스 | 배포/연결 기준은 미정 |
| `.github/workflows/` | CI/CD 워크플로우 | `deploy-dev.yml` |
| `tests/` | 테스트 | 현재 `test_cors.py` |

---

## 4. 변경 규칙 (이 레포에서 “같이 바뀌어야 하는 것”)

1) **헬스체크 변경**
- `/health` 경로 변경 시:
  - `render.yaml`의 `healthCheckPath` 영향 가능

2) **Docker/Compose 빌드 경로 변경**
- `docker/api.Dockerfile` 변경 시:
  - `infra/docker-compose.yml` 참조 점검

3) **정적 HTML 서빙 경로 변경**
- `apps/web-html/` 변경 시:
  - `apps/api/main.py` StaticFiles 설정 영향 가능
  - `apps/web-html/js/config.js` 영향 가능

4) **DB/영속성 레이어 변경**
- `adapters/persistence/*` 변경 시:
  - `apps/api/startup.py` 영향 가능
  - `scripts/migrate_*.py` 영향 가능

5) **정적 데이터 스키마 변경**
- `data/json/*.json` 변경 시:
  - 관련 API 코드 영향 가능

---

## 5. 환경변수/시크릿 취급 규칙

- 시크릿 값(API 키/DB URI/토큰)은 하드코딩 금지
- `.env` 또는 배포 플랫폼에서 주입
- 로그에 민감정보 출력 금지

---

## 6. Fail-fast 규칙 (운영 안정성)

- 필수 설정 누락 시 즉시 에러
- `/health`는 정상/비정상 명확 구분
- DB 초기화 실패 시 명확한 예외/로그
- 마이그레이션 실패 시 non-zero exit

---

## 7. 미정/암묵적(⚠️)

- `apps/api/`: dependencies vs deps 역할
- `docs/scratch/`: 분류 정책
- `html/app/web/`: 빌드/배포 관계
- `packages/db`, `packages/rag`: import 관계
- `tests/`: 구조/컨벤션
- 루트 기타 스크립트 유지 여부

### ⚠️ 티켓 정의 위치 기준
- GitHub Issue vs docs/tickets 기준은 섹션 9에서 정의

### ⚠️ Billing / Token / BO / Moderation 데이터 기준
- 스키마/흐름/정합성 전략은 섹션 10~11 참고

### ⚠️ 관측 / 레이트리밋 / 백업 기준
- 최소 기준은 섹션 12 참고

---

## 8. AI 도구 작업 지침 (필수)

### 8.1 작업 순서
1) SSOT 기준 해석
2) 영향 경로 확인
3) 변경 파일 목록 고정 후 수정
4) 실행 가능 여부 확인
5) 커밋 메시지 명확화

### 8.2 금지 사항
- 존재하지 않는 구조 가정 금지
- SSOT와 충돌 규칙 추가 금지
- 시크릿 삽입 금지
- scratch를 기준 문서로 승격 금지

### 8.3 커밋 단위 규칙
- 하나의 의도만 포함
- 대량 변경 시 영향 범위 명시

### 8.4 티켓 기반 개발 원칙

- 작업 시작 시 티켓 텍스트를 요구사항의 단일 진실로 간주
- 티켓에 없는 기능/스키마/엔드포인트 추가 금지
- 위험 변경은 SSOT 기준 없으면 중단 후 갱신 요청
- 핫픽스와 기능 개발은 반드시 분리

---

## Canonical Documentation

- **docs/SSOT.md** is the top-level source of truth.
- **docs/ARCHITECTURE.md** is the canonical system architecture document.
- **docs/AI_ENTRYPOINT.md** defines the canonical AI reading order.
- **docs/AI_AGENT_RULES.md** defines agent behavior constraints.
- **docs/DEVELOPMENT_GUIDE.md** defines the development workflow.
- **docs/architecture/** is supporting/reference material, not the top-level canonical source.
- **docs/scratch/** is temporary/non-canonical.

---

## AI Reading Order

1. docs/SSOT.md
2. docs/ARCHITECTURE.md
3. docs/AI_AGENT_RULES.md
4. docs/DEVELOPMENT_GUIDE.md
5. docs/AI_ENTRYPOINT.md
6. Assigned ticket under docs/tickets/
7. Related formal analysis under docs/analysis/

---

## Documentation Structure Lock

- **Allowed:**
  - create/update ticket files under docs/tickets/
  - create/update formal analysis under docs/analysis/
  - create temporary notes under docs/scratch/
- **Not allowed:**
  - introducing new documentation systems/folders without explicit request
  - changing docs folder structure during normal ticket work
- Structural changes are allowed only in dedicated documentation/system sessions.

---

## 9. 티켓 소스 및 실행 스펙 기준

### 9.1 단일 진실
- GitHub Issue 본문이 단일 진실

### 9.2 docs/tickets 사용 시

파일명:
T-XXX_설명.md

포함 항목:
- 목적
- 범위
- 금지 사항
- 완료 조건 (AC)
- 테스트 기준

### 9.3 우선순위
- 티켓 우선
- 단, SSOT 충돌 시 SSOT 우선

---

## 10. Billing & Token 기준 (최소)

### 10.1 Stripe 정기결제
- Webhook 이벤트 기준 동기화
- UI 완료만으로 확정하지 않음

### 10.2 token_ledger 최소 필드
- credit / debit
- source
- ref_id
- before
- after
- created_at

### 10.3 멱등성 전략
- idempotency key 사용
- 구현은 티켓에서 정의

### 10.4 원자적 업데이트
- 동시성에서 음수/중복 차감 방지
- 구현은 티켓에서 정의

---

## 11. Policy / Moderation / BO 기준 (최소)

### 11.1 차단 최소 필드
- reason_code
- detail
- blocked_at
- blocked_by

### 11.2 audit_log
- 누가
- 언제
- 무엇을
- 왜

### 11.3 role 최소 기준
- admin
- operator

---

## 12. 운영 안정성 기준 (최소)

### 12.1 관측
- 요청 비용
- 토큰 사용량
- 오류율
- 응답시간

### 12.2 Rate Limit
- 폭주 방지 기준 존재
- 수치는 티켓에서 정의

### 12.3 백업/복구
- 일 1회 스냅샷
- 복구 절차 문서화

---

문서 끝.