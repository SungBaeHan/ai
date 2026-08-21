# TRPG 프론트엔드 API Base URL 잔존 문제 조사 보고서

**조사일:** 2026-08-21  
**대상 현상:** `trpg.arcanaverse.ai/my` 에서 Google OAuth 후 `POST http://localhost:8000/v1/auth/google` ERR_CONNECTION_REFUSED  
**전제:** 이전 수정 — `config.js`, `session.js`, `home.html`, `chat.html`에 `trpg.arcanaverse.ai` 추가 완료  
**현재 상태:** 수정 없음 (조사 전용)

---

## 1. 전체 검색 결과

### 1-1. `localhost:8000` 잔존 위치 (12개)

```
apps/web-html/chat.html:182          → 이전 수정에서 처리됨 (trpg 조건 있음)
apps/web-html/home.html:125          → 이전 수정에서 처리됨 (trpg 조건 있음)
apps/web-html/js/config.js:11        → 이전 수정에서 처리됨 (trpg 조건 있음)
apps/web-html/js/config.js:20        → ASSET_BASE 로컬용, isProd 로직 동일하게 적용됨
apps/web-html/my.html:232            ← ★ 미수정, trpg 조건 없음
apps/web-html/my.html:264            ← ★ 미수정, trpg 조건 없음
apps/web-html/my.html:358            ← ★ 미수정, trpg 조건 없음
apps/web-html/my_list.html:96        ← ★ 미수정, trpg 조건 없음
apps/web-html/personas.html:579      ← ★ 미수정, trpg 조건 없음
apps/web-html/search.html:150        ← ★ 미수정, trpg 조건 없음
apps/web-html/static/js/session.js:7 → 이전 수정에서 처리됨 (trpg 조건 있음)
apps/web-html/world.html:182         ← ★ 미수정, trpg 조건 없음
```

**미수정 파일: 5개 파일, 6개 위치** (`my.html`에만 3개)

### 1-2. `window.location.hostname` 검사 위치 전체

| 파일 | 위치 | trpg 포함 여부 |
|------|------|---------------|
| `js/config.js` | line 5 (host 추출), line 7 (isProd) | ✅ 수정 완료 |
| `static/js/session.js` | line 3–5 (getApiBaseUrl) | ✅ 수정 완료 |
| `home.html` | line 121–123 | ✅ 수정 완료 |
| `chat.html` | line 178–180 | ✅ 수정 완료 |
| `chat.html` | line 1062–1063 (isLocal 체크, 별도 목적) | 무관 |
| `home.html` | line 870–871 (isLocal 체크, 별도 목적) | 무관 |
| **`my.html`** | **line 229–230** | ❌ trpg 없음 |
| **`my.html`** | **line 261–262** | ❌ trpg 없음 |
| **`my.html`** | **line 355–356** | ❌ trpg 없음 |
| **`my_list.html`** | **line 93–94** | ❌ trpg 없음 |
| **`personas.html`** | **line 576–577** | ❌ trpg 없음 |
| **`search.html`** | **line 147–148** | ❌ trpg 없음 |
| **`world.html`** | **line 179–180** | ❌ trpg 없음 |

### 1-3. `/v1/auth/google` 참조 위치

```
apps/web-html/my.html:299   fetch(`${API_BASE_URL}/v1/auth/google`, ...)
```

전체 `apps/web-html/`에서 유일한 1개 위치. `my.html` 단독.

---

## 2. `my` 페이지 Google 로그인 흐름 추적

### 전체 흐름

```
① Google Identity Services SDK (https://accounts.google.com/gsi/client)
   → Google 인증 팝업/리다이렉트 처리
   → 콜백: handleGoogleLogin(response)

② handleGoogleLogin(response) [my.html line 295]
   ├─ response.credential = Google ID Token (JWT)
   ├─ 사용할 API URL 결정: 스코프에서 가장 가까운 const API_BASE_URL
   │    → my.html line 228–232 (외부 스크립트 블록의 top-level const)
   │    → hostname 체크: arcanaverse.ai | www.arcanaverse.ai 만 확인
   │    → trpg.arcanaverse.ai → else → "http://localhost:8000"
   └─ fetch(`${API_BASE_URL}/v1/auth/google`, POST)  [line 299]
        → 실제 URL: http://localhost:8000/v1/auth/google
        → ERR_CONNECTION_REFUSED
```

### `handleGoogleLogin`이 참조하는 `API_BASE_URL`의 정확한 위치

```javascript
// my.html line 226–232: 메인 <script> 블록 최상단
<script>
  const API_BASE_URL =                        // ← 이 변수가 문제
    window.location.hostname === "arcanaverse.ai" ||
    window.location.hostname === "www.arcanaverse.ai"
      ? "https://api.arcanaverse.ai"
      : "http://localhost:8000";              // trpg에서는 이 값
```

`handleGoogleLogin`(line 295)은 이 `<script>` 블록 안에 선언되어 있으므로, **클로저로 이 `const API_BASE_URL` = `"http://localhost:8000"`을 그대로 사용한다.**

`window.API_BASE_URL` (line 16, 하드코딩 `'https://api.arcanaverse.ai'`)는 **로컬 `const`에 의해 완전히 가려진다.** `const`는 블록/함수 스코프에서 전역 프로퍼티보다 우선한다.

---

## 3. `trpg.arcanaverse.ai`에서 여전히 `localhost:8000`이 선택되는 정확한 원인

### `my.html` 안에만 3개의 독립 `API_BASE_URL` 선언이 존재

| 선언 위치 | 스코프 | 사용처 | trpg 포함 |
|-----------|--------|--------|-----------|
| line 228–232 | 외부 `<script>` 블록 최상단 (`const`) | `handleGoogleLogin` (POST /v1/auth/google) | ❌ |
| line 260–264 | `getUserInfo()` 함수 내부 (`const`) | `validate-session` 호출 | ❌ |
| line 354–358 | `updateUIFromSession()` 함수 내부 (`const`) | `validate-session` 호출 | ❌ |

세 선언 모두 동일한 패턴:

```javascript
const API_BASE_URL =
  window.location.hostname === "arcanaverse.ai" ||
  window.location.hostname === "www.arcanaverse.ai"  // trpg 없음
    ? "https://api.arcanaverse.ai"
    : "http://localhost:8000";
```

`trpg.arcanaverse.ai`에서 접속하면 세 선언 모두 `"http://localhost:8000"`으로 평가된다.

---

## 4. 브라우저 캐시 문제인지 코드 문제인지

**코드 문제다.** 이유:

1. **`my.html`은 이전 수정 대상에 포함되지 않았다.** `config.js`, `session.js`, `home.html`, `chat.html`만 수정되었고 `my.html`은 그대로다.

2. **캐시 문제라면** 이전 수정 대상 파일들(`home.html` 등)도 동일하게 캐시됐을 것이다. 그러나 보고된 에러는 `my.html` 의 `/v1/auth/google` 엔드포인트에서만 발생한다 — `home.html`의 캐릭터 목록 API가 아니다.

3. `my.html`의 `const API_BASE_URL` (line 228)은 수정된 적이 없으므로 **캐시와 무관하게 항상 `localhost:8000`을 반환한다.**

4. Cloudflare Pages는 정적 파일을 CDN 엣지에 캐시할 수 있으나, 새 배포 시 자동 purge가 이루어진다. 그러나 `my.html`은 새 배포에서도 여전히 잘못된 코드를 포함하고 있다.

---

## 5. 동일한 문제가 있는 파일 전체 목록

### 미수정 파일 (trpg.arcanaverse.ai에서 localhost:8000 사용)

| 파일 | 미수정 위치 | 영향받는 기능 |
|------|-------------|---------------|
| `my.html` | line 228–232 | Google 로그인 POST /v1/auth/google **★ 현재 에러 원인** |
| `my.html` | line 260–264 | getUserInfo() → validate-session |
| `my.html` | line 354–358 | updateUIFromSession() → validate-session |
| `my_list.html` | line 92–96 | My List 데이터 로드 전체 |
| `personas.html` | line 575–579 | 페르소나 목록 로드 전체 |
| `search.html` | line 146–150 | 검색 API 전체 |
| `world.html` | line 178–182 | 월드 상세 데이터 전체 |

### 정상 동작 파일 (이전 수정 또는 구조적으로 안전)

| 파일 | 이유 |
|------|------|
| `home.html` | 이전 수정 완료 (line 121–123에 trpg 추가됨) |
| `chat.html` | 이전 수정 완료 (line 178–180에 trpg 추가됨) |
| `game.html` | 로컬 `const` 재선언 없음. `window.API_BASE_URL = 'https://api.arcanaverse.ai'` (하드코딩) 전역 참조 |
| `create/character.html` | `const API_BASE_URL = getApiBaseUrl()` 사용 → session.js 수정 효과 적용됨 |
| `create/game.html` | `const API_BASE_URL = getApiBaseUrl()` 사용 → session.js 수정 효과 적용됨 |
| `create/world.html` | `const API_BASE_URL = getApiBaseUrl()` 사용 → session.js 수정 효과 적용됨 |
| `create/index.html` | `const API_BASE_URL` 선언 없음, API 호출 없음 |
| `js/config.js` | 이전 수정 완료 |
| `static/js/session.js` | 이전 수정 완료 |

---

## 요약

| 항목 | 내용 |
|------|------|
| **현재 에러 원인** | `my.html` line 228의 `const API_BASE_URL`에 `trpg.arcanaverse.ai` 미포함 |
| **영향 범위** | 5개 파일(my.html 3곳, my_list.html, personas.html, search.html, world.html) |
| **캐시 문제 여부** | 아님. 코드 자체가 미수정 상태 |
| **수정 방식** | 각 파일의 hostname 비교에 `trpg.arcanaverse.ai` 추가 (이전 수정과 동일 패턴) |
| **create/* 페이지** | session.js의 `getApiBaseUrl()` 경유 → 이미 정상 |
| **game.html** | 하드코딩 + 로컬 재선언 없음 → 이미 정상 |
