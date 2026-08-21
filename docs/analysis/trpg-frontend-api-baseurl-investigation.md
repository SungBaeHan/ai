# TRPG 프론트엔드 Production API Base URL 조사 보고서

**조사일:** 2026-08-21  
**대상 현상:** `https://trpg.arcanaverse.ai` 접속 시 브라우저 Console에 `[API BASE URL]: http://localhost:8000` 출력  
**현재 상태:** 수정 없음 (조사 전용)

---

## 1. API Base URL 결정 로직 전체 구조

프론트엔드는 **세 개의 독립적인 레이어**에서 API Base URL을 각자 결정하며, 이들이 서로 일치하지 않아 혼란이 발생한다.

### 레이어 1: `config.js` (전역 초기화)

**파일:** `apps/web-html/js/config.js` (line 5–11)

```javascript
const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';
const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai';
const API_BASE = isProd
  ? 'https://api.arcanaverse.ai'
  : 'http://localhost:8000';
```

- `window.API_BASE_URL`과 `window.API_BASE`를 설정
- 단, `window.API_BASE_URL`이 이미 설정되어 있으면 **덮어쓰지 않음** (line 24)

### 레이어 2: 각 HTML 파일 상단 인라인 스크립트 (하드코딩)

`config.js` 로드 **이후** 별도 `<script>` 블록으로 하드코딩:

```javascript
window.API_BASE_URL = 'https://api.arcanaverse.ai';
window.API_BASE = 'https://api.arcanaverse.ai';
```

대상 파일: `home.html`, `chat.html`, `game.html`, `create/character.html`, `create/game.html`, `create/world.html`, `create/index.html`

이 블록이 실행되는 시점에 config.js의 `window.API_BASE_URL`이 이미 `http://localhost:8000`으로 설정되어 있더라도, 여기서 **강제 덮어쓰기**하여 `https://api.arcanaverse.ai`로 교정된다.

### 레이어 3: 각 HTML 파일 하단 메인 인라인 스크립트 (로컬 변수)

각 HTML 파일의 메인 스크립트 블록 안에서 **로컬 `const`로 다시 정의**:

```javascript
// home.html line 120-124, chat.html line 177-181
const API_BASE_URL =
  window.location.hostname === "arcanaverse.ai" ||
  window.location.hostname === "www.arcanaverse.ai"
    ? "https://api.arcanaverse.ai"
    : "http://localhost:8000";
```

이 로컬 `const API_BASE_URL`이 **레이어 2의 `window.API_BASE_URL`을 완전히 가린다.** 모든 `fetch()` 호출은 이 로컬 변수를 참조하므로, `console.log('[API BASE URL]:', API_BASE_URL)` 역시 이 값을 출력한다.

### 레이어 4: `session.js` (create/* 페이지에서 사용)

**파일:** `apps/web-html/static/js/session.js` (line 2–7)

```javascript
function getApiBaseUrl() {
  return window.location.hostname === "arcanaverse.ai" ||
    window.location.hostname === "www.arcanaverse.ai"
    ? "https://api.arcanaverse.ai"
    : "http://localhost:8000";
}
```

`create/character.html`, `create/world.html`에서 `getApiBaseUrl()`로 호출.

---

## 2. `http://localhost:8000` 값의 출처

`[API BASE URL]: http://localhost:8000`을 출력하는 정확한 코드 위치:

**`home.html` line 872:**
```javascript
console.log('[API BASE URL]:', API_BASE_URL);
```

여기서 `API_BASE_URL`은 **레이어 3**의 로컬 `const`다 (line 120-124).

`trpg.arcanaverse.ai` hostname은:
- `"arcanaverse.ai"` 와 일치하지 않음
- `"www.arcanaverse.ai"` 와 일치하지 않음

따라서 삼항 연산자의 else 분기 → `"http://localhost:8000"` 이 반환된다.

동일 패턴이 `chat.html` line 177-181에도 있다.

---

## 3. 파일별 실행 순서와 변수 우선순위

### `home.html` 실행 순서

| 순서 | 코드 위치 | 실행 결과 |
|------|-----------|-----------|
| 1 | `<script src="/js/config.js">` (line 11) | `window.API_BASE_URL = 'http://localhost:8000'` (trpg.arcanaverse.ai 불일치) |
| 2 | 인라인 `<script>` (line 16-17) | `window.API_BASE_URL = 'https://api.arcanaverse.ai'` (하드코딩 덮어씌우기) |
| 3 | 메인 `<script>` (line 120-124) | `const API_BASE_URL = 'http://localhost:8000'` (로컬 변수, hostname 불일치) |
| 4 | `console.log` (line 872) | `[API BASE URL]: http://localhost:8000` 출력 |
| 5 | 모든 `fetch()` 호출 | `http://localhost:8000/v1/...` 로 요청 |

### `chat.html` 실행 순서 (동일 패턴)

| 순서 | 코드 위치 | 실행 결과 |
|------|-----------|-----------|
| 1 | `<script src="/js/config.js">` (line 17) | `window.API_BASE_URL = 'http://localhost:8000'` |
| 2 | 인라인 `<script>` (line 20-21) | `window.API_BASE_URL = 'https://api.arcanaverse.ai'` |
| 3 | 메인 `<script>` (line 177-181) | `const API_BASE_URL = 'http://localhost:8000'` |
| 4 | 모든 `fetch()` 호출 | `http://localhost:8000/v1/...` 로 요청 |

### `game.html` (정상 동작 — 다른 패턴)

`game.html`은 **로컬 `const API_BASE_URL`을 재선언하지 않는다.** 메인 스크립트(line 672~)에서 사용하는 `API_BASE_URL`은 레이어 2에서 설정된 `window.API_BASE_URL = 'https://api.arcanaverse.ai'` (하드코딩)를 전역으로 참조한다. → **game.html은 정상적으로 Production API를 사용 중**

---

## 4. 환경 구분 현황

### 개발 환경 감지 기준 (현재)

모든 파일이 아래 두 가지 중 하나를 사용:

**방식 A (`config.js`, `session.js`):**
```javascript
hostname === 'arcanaverse.ai' || hostname === 'www.arcanaverse.ai'
```

**방식 B (각 HTML 인라인):**
```javascript
window.location.hostname === "arcanaverse.ai" || window.location.hostname === "www.arcanaverse.ai"
```

두 방식 모두 **동일한 로직**, 동일한 취약점.

### Cloudflare Pages 배포 구조

- **프론트엔드:** Cloudflare Pages → `trpg.arcanaverse.ai` (`dev` 브랜치를 Production으로 배포)
- **백엔드 API:** Oracle VM + Docker + nginx → `api.arcanaverse.ai`
- **배포 자동화:** `.github/workflows/deploy-dev.yml` → `dev` 브랜치 push 시 Oracle VM에 API 배포

Cloudflare Pages에는 별도 환경 변수 주입 설정이 없다. 빌드 없이 정적 HTML/JS를 그대로 서빙하므로 런타임에서 hostname 체크에 의존한다.

---

## 5. Production에서 `https://api.arcanaverse.ai`가 선택되지 않는 정확한 원인

**근본 원인:** hostname 매칭 목록에 `trpg.arcanaverse.ai`가 누락되어 있다.

사이트 도메인이 `arcanaverse.ai` → `trpg.arcanaverse.ai`로 변경(또는 추가)되었으나, 환경 감지 조건이 업데이트되지 않았다.

```javascript
// 현재 (불완전)
hostname === 'arcanaverse.ai' || hostname === 'www.arcanaverse.ai'
//                              ↑ trpg.arcanaverse.ai 없음

// trpg.arcanaverse.ai 접속 시
// → isProd = false
// → API_BASE = 'http://localhost:8000'
```

이 패턴이 3개 파일, 4개 위치에 중복 존재한다:
1. `apps/web-html/js/config.js` (line 7)
2. `apps/web-html/static/js/session.js` (line 3-4)
3. `apps/web-html/home.html` (line 121-123)
4. `apps/web-html/chat.html` (line 178-180)

---

## 6. 수정이 필요한 파일과 설정

### 프론트엔드 (API URL 결정 로직)

| 파일 | 위치 | 수정 내용 |
|------|------|-----------|
| `apps/web-html/js/config.js` | line 7 | `trpg.arcanaverse.ai` 추가 |
| `apps/web-html/static/js/session.js` | line 3-4 | `trpg.arcanaverse.ai` 추가 |
| `apps/web-html/home.html` | line 121-123 | `trpg.arcanaverse.ai` 추가 |
| `apps/web-html/chat.html` | line 178-180 | `trpg.arcanaverse.ai` 추가 |

**수정 예시 (`config.js` line 7):**
```javascript
// 현재
const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai';

// 수정 후
const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai' || host === 'trpg.arcanaverse.ai';
```

### 백엔드 CORS 설정

**파일:** `apps/api/main.py` (line 39-41)

현재 ALLOWED_ORIGINS:
```python
"https://arcanaverse.ai",
"https://www.arcanaverse.ai",
```

`trpg.arcanaverse.ai`에서 오는 요청은 현재 CORS 차단 대상이다. `https://trpg.arcanaverse.ai`를 ALLOWED_ORIGINS에 추가해야 한다.

---

## 7. 수정 시 localhost 개발환경에 미치는 영향

**영향 없음.** 모든 수정은 `trpg.arcanaverse.ai` 조건을 추가하는 것이며, 기존 로직은 그대로 유지된다.

- `localhost` 개발 환경: hostname이 `arcanaverse.ai`/`www.arcanaverse.ai`/`trpg.arcanaverse.ai` 중 어느 것도 아니므로 여전히 `http://localhost:8000` 사용
- `arcanaverse.ai` (기존 도메인 접속 시): 기존대로 Production API 사용

단, 개발 환경에서 **특정 도메인이 필요한 기능**(예: OAuth 콜백)을 테스트하려면 `/etc/hosts` 수정이 필요할 수 있으나, 이는 현재 구조와 무관하다.

---

## 8. CORS 및 추가 변경 필요 사항

### CORS (필수 수정)

`apps/api/main.py` ALLOWED_ORIGINS에 `trpg.arcanaverse.ai`가 없으므로, 현재 브라우저는:
- Preflight OPTIONS 요청이 CORS 오류로 실패할 가능성이 있음
- 단, 현재 API 호출 자체가 `localhost:8000`으로 잘못 향하고 있어 CORS 오류 자체가 실제로 발생하지 않는 상태 (잘못된 URL → 연결 실패)

URL 수정 후 CORS 오류가 새로 발생하게 되므로 **반드시 함께 수정**해야 한다.

### nginx (불필요)

`infra/nginx/conf.d/` 에는 `api.arcanaverse.ai`와 `nlp-api.arcanaverse.ai` 설정만 있다. `trpg.arcanaverse.ai`는 Cloudflare Pages에서 직접 서빙하므로 nginx 변경 불필요.

### Google OAuth (확인 필요)

Google OAuth의 허용 redirect URI 목록에 `https://trpg.arcanaverse.ai`가 포함되어 있어야 한다. 코드(`apps/api/routes/auth_google.py`)에서 redirect_uri가 동적으로 hostname에 따라 생성되는지, 하드코딩인지 확인이 필요하다.

---

## 요약

| 항목 | 내용 |
|------|------|
| **근본 원인** | `trpg.arcanaverse.ai` hostname이 Production 도메인 목록에 누락됨 |
| **영향 받는 파일** | `config.js`, `session.js`, `home.html`, `chat.html` |
| **정상 동작 중인 파일** | `game.html` (로컬 재선언 없이 `window.API_BASE_URL` 하드코딩 참조) |
| **CORS 차단 여부** | URL 수정 후 발생 예정 — `main.py` ALLOWED_ORIGINS에 추가 필요 |
| **localhost 영향** | 없음 |
| **Cloudflare 설정 변경** | 불필요 |
