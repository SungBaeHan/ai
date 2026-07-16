# v1 복구 상태 점검 리포트

- **점검 일시:** 2026-06-14
- **점검 대상 브랜치:** `dev` (`d316b7e`)
- **점검 방식:** Git 상태 확인, 프로덕션 엔드포인트 프로브, 코드 정적 분석 (코드/설정 변경 없음)
- **배경:** `git reset HEAD^^^^^^^` 후 `git push origin +dev`로 최근 변경분 제거 및 데모용 v1 복귀

---

## 1. 결론

- **상태:** Git 브랜치 복구는 **정상 완료**. 로컬/원격 `dev`·`main` 모두 `d316b7e`로 일치하며 working tree clean. 프로덕션 API·프론트는 v1 기준과 **대체로 정합**하나, 일부 My List 경로와 라우트 순서 버그가 데모 시나리오를 제한함.
- **데모 가능 여부:** **조건부 진행**
- **가장 큰 리스크:** `My List > My Favorite > 캐릭터`가 호출하는 `GET /v1/characters/my`가 라우트 순서 문제로 **400 (Invalid character id)** 반환. 데모 시 **My Create > 캐릭터** 경로(`/api/my-create/characters`) 위주로 진행해야 함.

### 데모 권장 시나리오 (진행 가능 범위)

| 영역 | 권장 | 비권장/주의 |
|------|------|-------------|
| 홈·검색·캐릭터/세계관/게임 탐색 | ✅ | — |
| 로그인 (`/my`, Google OAuth) | ✅ (실제 Google 로그인 필요) | — |
| My List > My Create > 캐릭터 | ✅ | — |
| My List > My Favorite > 캐릭터 | ❌ | `/v1/characters/my` 400 버그 |
| My List > My Create > 세계관/게임 | ⚠️ | 사용자 생성 목록이 아닌 **전체 공개 목록** 표시 |
| `html/app/web` React 스캐폴드 | ❌ | 빌드 파이프라인 없음, 프로덕션 미사용 |

---

## 2. Git 상태

### 2.1 브랜치·커밋

| 항목 | 결과 |
|------|------|
| 현재 브랜치 | `dev` |
| HEAD | `d316b7e` — `[MS-01] FEAT-001_My-Create-Character-List-UI` (2026-04-09) |
| `origin/dev` | `d316b7e` — **로컬과 동일** |
| `main` | `d316b7e` — **dev와 동일** |
| Working tree | **clean** (uncommitted 변경 없음) |
| `origin/dev` 대비 ahead/behind | 0 / 0 |

### 2.2 reset으로 제거된 커밋 (7개)

`d316b7e..79915c6` 구간이 원격에서 제거됨:

```
79915c6 ci: add issue to codex smoke test workflow
f4eb542 feat: add my create games api
0027977 chore: validate utf-8 korean text integrity
65285ff fix: recover broken korean messages in my_create api
f980427 feat: add my create world api
7c7444d docs: add my create world and game api tickets
582dbca ai workflow 변경 테스트
```

**되돌아간 기준점:** v1 데모 범위로 보이는 `FEAT-001_My-Create-Character-List-UI` 커밋. My Create **캐릭터** UI·API 연동까지 포함된 상태.

### 2.3 reflog 요약

```
HEAD@{0}: reset: moving to HEAD^^^^^^^  → d316b7e
HEAD@{1}: checkout: moving from main to dev  (이전 HEAD: 79915c6)
```

force push 이후 로컬·원격 정합성은 확인됨.

### 2.4 추적 중이나 데모와 무관한 파일

`html/app/web/src/` 하위 React 파일 3개가 **현재 HEAD에 포함**되어 있으나, `package.json`·빌드 설정 없음. 프로덕션 프론트는 `apps/web-html/` 정적 HTML이며 Cloudflare Pages로 서빙됨.

---

## 3. 프론트 상태

### 3.1 빌드 가능 여부

| 구분 | 결과 | 비고 |
|------|------|------|
| `apps/web-html/` (실제 프로덕션 프론트) | **빌드 단계 없음** | 정적 HTML/JS. 배포 = 파일 서빙 |
| `html/app/web/` (React 스캐폴드) | **빌드 불가** | `package.json` 없음, placeholder UI만 존재 |

로컬에서 npm/vite 빌드 검증은 수행하지 않았으나, 데모 대상 프론트는 빌드가 필요 없는 구조임.

### 3.2 프로덕션 페이지 접근 (2026-06-14 프로브)

Cloudflare Pages는 **확장자 없는 clean URL**을 사용. `*.html` 직접 접근 시 308 리다이렉트 발생.

| 경로 | HTTP | 비고 |
|------|------|------|
| `https://www.arcanaverse.ai/` | 200 | 루트 정상 |
| `https://www.arcanaverse.ai/home` | 200 | 홈 |
| `https://www.arcanaverse.ai/my` | 200 | My/로그인 |
| `https://www.arcanaverse.ai/my_list` | 200 | My List |
| `https://www.arcanaverse.ai/characters` | 200 | 캐릭터 (라우팅 존재) |
| `https://www.arcanaverse.ai/login` | 200 | 로그인 관련 |
| `https://www.arcanaverse.ai/home.html` | 308 | clean URL로 리다이렉트 |

### 3.3 배포된 API Base URL

프로덕션 `https://www.arcanaverse.ai/js/config.js` 확인 결과:

- Production: `https://api.arcanaverse.ai` (**`/api` suffix 없음**)
- Local: `http://localhost:8000`

현재 `dev` 브랜치 코드(`apps/web-html/js/config.js`)와 **일치**.

### 3.4 로컬 프론트 개발 환경

- 정적 파일이므로 로컬 HTTP 서버만 있으면 확인 가능
- API 호출은 `localhost:8000` 백엔드 필요 (아래 4절 참고)

---

## 4. 백엔드/API 상태

### 4.1 로컬 빌드·실행

| 항목 | 결과 |
|------|------|
| `pip` + `fastapi` | **미설치** — `from apps.api.main import app` 실패 |
| Docker Desktop | **미실행** — `docker build` 연결 실패 |
| `requirements.txt` | 존재, FastAPI/uvicorn 등 정의됨 |
| `infra/docker-compose.yml` | API + Qdrant 구성 정상 (nginx web 컨테이너는 주석 처리) |

로컬 백엔드 빌드/실행은 **이 환경에서 검증 불가**. 프로덕션 API 프로브로 대체 검증함.

### 4.2 프로덕션 API 프로브

| 엔드포인트 | HTTP | 정상/버그 판단 |
|------------|------|----------------|
| `GET /health` | 200 | ✅ 정상 |
| `GET /v1/characters?limit=1` | 200 | ✅ 정상 |
| `GET /v1/worlds?limit=1` | 200 | ✅ 정상 |
| `GET /v1/games?limit=1` | 200 | ✅ 정상 |
| `POST /v1/auth/validate-session` (body `{}`) | 401 | ✅ 비로그인 시 정상 |
| `GET /api/my-create/characters?limit=1` | 401 | ✅ 인증 필요 (엔드포인트 존재) |
| `GET /api/my/characters?limit=1` | 401 | ✅ 인드포인트 존재 |
| `GET /api/my-create/worlds` | 404 | ✅ v1에 없음 (reset으로 제거된 API와 일치) |
| `GET /api/my-create/games` | 404 | ✅ v1에 없음 |
| `GET /v1/characters/my?skip=0&limit=50` | 400 `Invalid character id` | ❌ **버그** |
| `GET /v1/characters/count` | 400 `Invalid character id` | ❌ **버그** (동일 원인) |
| `GET /v1/my/characters` | 404 | ✅ 미구현 (대체: `/api/my/characters`) |

프로덕션 API는 reset 제거 대상(world/game my-create)이 **404**인 점에서 현재 `dev` 코드와 **정합**으로 보임. (force push 후 `deploy-dev.yml`이 실행되었다면 VM도 `d316b7e` 기준일 가능성 높음. GitHub CLI 미설치로 Actions 실행 이력은 미확인.)

### 4.3 nginx 라우팅

`infra/nginx/conf.d/api.arcanaverse.ai.conf`:

- `api.arcanaverse.ai` → `proxy_pass http://api:8000` (루트 프록시, **경로 rewrite 없음**)
- FastAPI가 `/v1/...`, `/api/...`를 직접 노출하는 구조와 일치

---

## 5. 인증/세션 상태

### 5.1 프론트 인증 흐름

- **로그인 페이지:** `apps/web-html/my.html` (`/my`)
- Google Identity Services → `POST /v1/auth/google`
- 세션 검증: `POST /v1/auth/validate-session` (body에 `user_info_v2` 토큰)
- 토큰 저장: 쿠키 `user_info_v2` + `localStorage` fallback

### 5.2 백엔드 쿠키·CORS (BUG-003 반영됨)

`apps/api/routes/auth_google.py`:

- `arcanaverse.ai` 호스트: `domain=.arcanaverse.ai`, `secure=True`, `samesite=none`
- 크로스 서브도메인(www ↔ api) 쿠키 공유 설정 **v1 HEAD에 포함**

`apps/api/main.py` CORS:

- `https://arcanaverse.ai`, `https://www.arcanaverse.ai` 및 localhost 포트 허용
- `allow_credentials=True`

### 5.3 HTTP 상태 코드 해석 (데모 기준)

| 코드 | 상황 | 판단 |
|------|------|------|
| 401 | validate-session, my-create API 무인증 호출 | ✅ 정상 |
| 400 | `/v1/characters/my`, `/v1/characters/count` | ❌ 라우트 버그 |
| 404 | `/api/my-create/worlds`, `/v1/my/characters` | ✅ v1 미구현 또는 의도적 |
| 502 | 이번 프로브에서 **미발견** | — |
| 308 | `*.html` → clean URL | ✅ Cloudflare/Pages 정상 |

---

## 6. API Base URL / nginx 라우팅 점검

### 6.1 `/api/backend/api/...` 이중 경로

- 코드베이스 전체 검색 결과: **해당 패턴 없음** ✅
- reset 이전 커밋(79915c6)의 `my_list.html`도 `https://api.arcanaverse.ai` + `/v1/...` 또는 `/api/my-create/...` 형태로 **이중 `/api/backend` 없음**

### 6.2 `/api` 중복 여부

| 패턴 | 위치 | 판단 |
|------|------|------|
| `API_BASE` = `https://api.arcanaverse.ai` | `apps/web-html/js/config.js` 등 | ✅ `/api` 없음 |
| `${API_BASE_URL}/v1/...` | 대부분 HTML | ✅ 정상 |
| `${API_BASE_URL}/api/my-create/characters` | `apps/web-html/my_list.html:275` | ✅ **의도적** — FastAPI `prefix="/api"` 라우터와 매칭 |

**최종 URL 예:** `https://api.arcanaverse.ai/api/my-create/characters` — nginx 전제와 **충돌 없음**.

### 6.3 환경별 Base URL 정리

| 환경 | 프론트 API Base | 백엔드 노출 |
|------|-----------------|-------------|
| Production | `https://api.arcanaverse.ai` | `api.arcanaverse.ai` (nginx → FastAPI:8000) |
| Local dev | `http://localhost:8000` | docker-compose `127.0.0.1:8000` |

---

## 7. 발견된 문제

### P1 — My Favorite 캐릭터 목록 API 라우트 충돌 (데모 차단 가능)

| 항목 | 내용 |
|------|------|
| **파일** | `apps/api/routes/characters.py` |
| **위치** | L166 `@router.get("/{character_id}")` 가 L206 `@router.get("/my")` **보다 앞**에 정의됨 |
| **증상** | `GET /v1/characters/my` → 400 `Invalid character id` (`character_id="my"`로 파싱) |
| **영향** | `apps/web-html/my_list.html:281` — `My Favorite` + `캐릭터` 탭 실패 |
| **원인** | FastAPI/Starlette 라우트 매칭 순서 — 동적 path가 정적 `/my`, `/count`를 가로챔 (`/count`도 동일 400) |
| **위험도** | **높음** (My Favorite 데모 시나리오) |
| **수정 제안** | `/my`, `/count` 등 정적 경로를 `/{character_id}` **위로** 이동. 또는 Favorite 탭을 `/api/my/characters`로 변경 |

### P2 — My Create 세계관/게임은 사용자 목록 미연동 (v1 한계)

| 항목 | 내용 |
|------|------|
| **파일** | `apps/web-html/my_list.html` |
| **위치** | L283–288 (`currentType === 'worlds'`, `'games'`) |
| **증상** | My Create 모드에서도 `GET /v1/worlds`, `GET /v1/games` **공개 전체 목록** 호출 |
| **원인** | reset으로 제거된 `my-create/worlds`, `my-create/games` API 미포함 (v1 범위) |
| **위험도** | **중간** (데모 스크립트가 “내가 만든 세계관”을 보여주려 하면 실패) |
| **수정 제안** | 데모에서 해당 탭 회피. 또는 제거된 API 커밋 재도입 |

### P3 — `html/app/web` React 스캐폴드 혼재

| 항목 | 내용 |
|------|------|
| **파일** | `html/app/web/src/App.tsx`, `pages/my/*.tsx` |
| **증상** | Git 추적 중이나 빌드·배포 파이프라인 없음, placeholder UI |
| **위험도** | **낮음** (프로덕션 미사용, 혼동만 유발) |
| **수정 제안** | 데모 후 별도 브랜치로 분리하거나 `.gitignore` 검토 (지금은 수정 금지) |

### P4 — 로컬 개발 환경 미구성

| 항목 | 내용 |
|------|------|
| **증상** | FastAPI 미설치, Docker Desktop 미실행 |
| **위험도** | **낮음** (프로덕션 데모에는 영향 없음) |
| **수정 제안** | 로컬 검증 필요 시 `pip install -r requirements.txt` 또는 Docker Desktop 기동 후 `infra/docker-compose.yml` up |

### P5 — 배포 워크플로 실행 이력 미확인

| 항목 | 내용 |
|------|------|
| **파일** | `.github/workflows/deploy-dev.yml` |
| **내용** | `dev` push 시 Oracle VM `scripts/deploy_from_git.sh dev` 실행 |
| **위험도** | **낮~중** (force push 후 VM이 갱신되지 않았다면 코드·운영 불일치 가능) |
| **판단** | API 프로브 결과가 v1 코드와 일치하여 **실제로는 배포된 것으로 추정** |
| **수정 제안** | GitHub Actions에서 최근 `Deploy to Oracle VM (dev)` 성공 여부 확인 |

---

## 8. 데모 전 최소 조치

데모 **당일** 코드 수정 없이 가능한 체크리스트:

1. **시나리오 확정:** Home → 캐릭터 채팅, `/my` Google 로그인, **My List > My Create > 캐릭터** 중심.
2. **회피:** My List > **My Favorite** > 캐릭터 (P1 버그).
3. **회피:** My List > My Create > 세계관/게임을 “내 작품 목록”으로 소개하지 않기 (P2).
4. **URL:** 데모 시 `https://www.arcanaverse.ai/home` 등 **clean URL** 사용 (`.html` 직접 링크 지양).
5. **로그인:** Google OAuth 동작 확인 — 시크릿/클라이언트 ID는 서버 `.env`에 의존 (`GOOGLE_CLIENT_ID`, `JWT_SECRET` 등).
6. **(선택)** GitHub Actions에서 force push 이후 deploy workflow **성공** 여부 1회 확인.

데모 **전에 수정이 허용**된다면 최소 1건:

- **P1 라우트 순서 수정** (`characters.py`에서 `/my`, `/count`를 `/{character_id}` 위로) — My Favorite 시나리오 복구.

---

## 9. 수정하면 안 되는 영역

분석 목적상 아래는 **이번 복구 검증에서 건드리지 않음**. 임의 변경 시 배포·인증이 깨질 수 있음.

| 영역 | 이유 |
|------|------|
| `origin/dev` Git 히스토리 | 이미 force push로 정리됨. 재force push는 협업·배포 이력 혼란 |
| 프로덕션 `.env` / `GOOGLE_CLIENT_ID`, `JWT_SECRET`, `MONGO_URI` | 인증·DB 연결 직결 |
| `infra/nginx/conf.d/api.arcanaverse.ai.conf` | 현재 API 라우팅 전제와 정합 |
| `apps/web-html/js/config.js`의 prod base URL | 배포 프론트와 이미 일치 |
| `auth_google.py` 쿠키 domain 설정 (BUG-003) | 크로스 서브도메인 로그인에 필수 |
| reset으로 제거된 7개 커밋의 **무분별한 cherry-pick** | v1 복구 목적과 상충. 필요 시 별도 계획 후 진행 |

---

## 부록 A — 환경 변수 요약

| 변수 | 용도 | 위치 | 비고 |
|------|------|------|------|
| `MONGO_URI`, `MONGO_DB_NAME` | DB | `.env`, `infra/.env`, `apps/api/config.py` | 로컬 `.env` 존재 (값 미기재) |
| `GOOGLE_CLIENT_ID` | Google OAuth aud 검증 | `auth_google.py` | 미설정 시 aud 검증 스킵 |
| `JWT_SECRET` | access_token JWT | `auth.py`, `auth_google.py` | 기본값 fallback 있음 — prod에서는 실제 시크릿 필요 |
| `AUTH_USER_INFO_V2_SECRET` | user_info_v2 토큰 | `config.py` | 기본값 존재 |
| `ASSET_BASE_URL` | 이미지 CDN | `config.py` | 기본 `https://img.arcanaverse.ai` |
| 프론트 API base | 런타임 | `config.js`, 각 HTML inline | hostname 기반 분기 |

dev/prod 충돌 포인트: 프론트는 hostname으로 API URL을 고정 분기하므로, **스테이징 도메인 없이** arcanaverse.ai / localhost 이원 구조. 중간 환경 URL 추가 시 `config.js` 및 CORS 동시 수정 필요.

---

## 부록 B — 제거된 기능 vs v1 잔존 기능

| 기능 | v1 (`d316b7e`) | 제거된 커밋 |
|------|----------------|-------------|
| My Create 캐릭터 API/UI | ✅ | — |
| My Create 세계관 API | ❌ | `f980427` |
| My Create 게임 API | ❌ | `f4eb542` |
| CI codex smoke workflow | ❌ | `79915c6` |
| 한글 메시지 복구 | ❌ | `65285ff` |

---

*본 문서는 분석 전용이며, 점검 시점 코드·프로덕션 응답을 기준으로 작성되었습니다.*
