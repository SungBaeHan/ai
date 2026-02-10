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

아래는 “동시 변경”이 필요할 수 있는 대표 연결점이다. (존재하는 파일 기준)

1) **헬스체크 변경**
- `/health` 경로(또는 health 라우트 동작)를 바꾸면:
  - `render.yaml`의 `healthCheckPath` 영향 가능

2) **Docker/Compose 빌드 경로 변경**
- `docker/api.Dockerfile` 또는 컨텍스트 변경 시:
  - `infra/docker-compose.yml` 참조를 함께 점검

3) **정적 HTML 서빙 경로 변경**
- `apps/web-html/` 경로/마운트 방식 변경 시:
  - `apps/api/main.py`의 StaticFiles 설정/라우팅 영향 가능
  - `apps/web-html/js/config.js`의 API Base URL 영향 가능

4) **DB/영속성 레이어 변경**
- `adapters/persistence/*` 변경 시:
  - `apps/api/startup.py` 및 라우트/서비스에서의 사용부 영향 가능
  - 관련 `scripts/migrate_*.py` 영향 가능

5) **정적 데이터 스키마 변경**
- `data/json/*.json` 구조 변경 시:
  - 이를 읽는 API 코드(주로 `apps/api/`) 영향 가능

---

## 5. 환경변수/시크릿 취급 규칙

- 시크릿 값(API 키/DB URI/토큰)은 **문서/코드에 하드코딩 금지**
- `.env` / 배포 플랫폼(Render/CI Secrets 등)로 주입한다.
- 로그(`docs/logs/`, 앱 로그)에는 민감정보 출력 금지

> 구체 변수명/값은 이 SSOT에서 **나열하지 않는다**. (레포 내 실제 config에서만 관리)

---

## 6. Fail-fast 규칙 (운영 안정성)

다음 상황에서는 “조용히 넘어가지 말고” 오류를 빠르게 노출한다.

- 부팅 시 필수 설정 누락: 즉시 에러 반환(기동 실패 또는 명시적 5xx)
- 헬스체크(`/health`)는 “정상/비정상”을 명확히 구분해 반환
- DB 연결/인덱스 초기화가 필수 전제라면:
  - `apps/api/startup.py`에서 실패 시 명확한 예외/로그를 남긴다
- 마이그레이션/일회성 스크립트(`scripts/migrate_*.py`)는:
  - 실패 시 즉시 non-zero exit / 원인 로그 출력

---

## 7. 미정/암묵적(⚠️) — 이 레포에서 아직 “기준이 문서화되지 않은 것”

아래 항목은 현재 구조상 존재하지만, 기준이 명확히 고정되어 있지 않다.  
**임의로 결정하지 말고**, 작업 시 “현행 코드/기존 동작”을 우선 확인한다.

- `apps/api/`: `dependencies/` vs `deps/` 역할·구분
- `docs/scratch/`: 명명·분류·보관 정책
- `html/app/web/`: 빌드 결과물 경로, API 프록시, 배포 대상과의 관계
- `packages/db`, `packages/rag`: API·다른 앱과의 실제 import/사용 관계
- `tests/`: 테스트 구조·실행 방식·컨벤션(단위/통합 등)
- 루트의 `structure.txt`, `str`, `infra_fix_qdrant.sh`: 유지 여부·용도

---

## 8. AI 도구(Codex/Cursor/Atlas) 작업 지침 (필수)

### 8.1 작업 순서
1) 변경 요청을 SSOT 기준으로 해석
2) 영향 경로(섹션 4 “변경 규칙”) 확인
3) 변경 파일 목록을 먼저 고정한 뒤 수정
4) 로컬/컨테이너 기준 실행 가능 여부를 확인(가능한 범위에서)
5) 커밋 메시지는 “무엇을/왜”가 드러나게 작성

### 8.2 금지 사항
- 존재하지 않는 파일/폴더를 “있다고 가정”하고 생성하지 말 것
- SSOT와 충돌하는 새로운 규칙을 임의로 추가하지 말 것
- 시크릿/토큰/키를 코드/문서에 삽입하지 말 것
- `docs/scratch/`를 “정식 문서”처럼 참조 기준으로 승격하지 말 것

### 8.3 커밋 단위 규칙
- 커밋은 “하나의 의도”만 담는다
- 문서 변경과 코드 변경이 함께 필요하면:
  - 원칙: 같은 커밋에 포함 가능(단, 목적이 하나일 때)
- 자동 생성/대량 변경은:
  - 반드시 변경 이유와 영향 범위를 커밋 메시지에 명시

---

문서 끝.
