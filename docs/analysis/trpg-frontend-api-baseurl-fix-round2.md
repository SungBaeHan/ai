# TRPG 프론트엔드 API Base URL 잔존 문제 수정 보고서 (Round 2)

**수정일:** 2026-08-21  
**근거 문서:** `trpg-frontend-api-baseurl-remaining-issues.md`  
**목적:** `trpg.arcanaverse.ai`의 모든 페이지에서 `https://api.arcanaverse.ai` 사용

---

## 1. 변경 파일 목록

| 파일 | 수정 위치 수 |
|------|------------|
| `apps/web-html/my.html` | 3곳 (line 229–231, 262–264, 357–359) |
| `apps/web-html/my_list.html` | 1곳 (line 93–95) |
| `apps/web-html/personas.html` | 1곳 (line 576–578) |
| `apps/web-html/search.html` | 1곳 (line 147–149) |
| `apps/web-html/world.html` | 1곳 (line 179–181) |

총 **5개 파일, 7개 위치** 수정.

---

## 2. 실제 변경 내용 (모든 위치 동일 패턴)

```diff
  const API_BASE_URL =
    window.location.hostname === "arcanaverse.ai" ||
-   window.location.hostname === "www.arcanaverse.ai"
+   window.location.hostname === "www.arcanaverse.ai" ||
+   window.location.hostname === "trpg.arcanaverse.ai"
      ? "https://api.arcanaverse.ai"
      : "http://localhost:8000";
```

### `my.html` 3곳 상세

| 위치 | 스코프 | 사용 함수 |
|------|--------|-----------|
| line 229–231 | 외부 `<script>` 최상단 | `handleGoogleLogin` → POST `/v1/auth/google` |
| line 262–264 | `getUserInfo()` 내부 | `validate-session` 호출 |
| line 357–359 | `updateUIFromSession()` 내부 | `validate-session` 호출 |

---

## 3. 검증 결과

### 3-1. `localhost:8000` 잔존 위치 전체 목록 (수정 후)

```
apps/web-html/chat.html:182          ✅ trpg 포함 (이전 수정)
apps/web-html/home.html:125          ✅ trpg 포함 (이전 수정)
apps/web-html/js/config.js:11        ✅ trpg 포함 (이전 수정)
apps/web-html/js/config.js:20        ✅ trpg 포함 (ASSET_BASE, isProd 동일 로직)
apps/web-html/my.html:233            ✅ trpg 포함 (이번 수정)
apps/web-html/my.html:266            ✅ trpg 포함 (이번 수정)
apps/web-html/my.html:361            ✅ trpg 포함 (이번 수정)
apps/web-html/my_list.html:97        ✅ trpg 포함 (이번 수정)
apps/web-html/personas.html:580      ✅ trpg 포함 (이번 수정)
apps/web-html/search.html:151        ✅ trpg 포함 (이번 수정)
apps/web-html/static/js/session.js:7 ✅ trpg 포함 (이전 수정)
apps/web-html/world.html:183         ✅ trpg 포함 (이번 수정)
```

`localhost:8000`을 사용하는 모든 12개 위치가 `trpg.arcanaverse.ai` 조건을 포함한다.

### 3-2. `trpg.arcanaverse.ai`가 빠진 분기가 더 이상 없는지

`window.location.hostname`을 사용하는 Production/localhost 분기 전체:

| 파일:위치 | trpg 포함 |
|-----------|-----------|
| `js/config.js:7` (isProd) | ✅ |
| `static/js/session.js:3–5` (getApiBaseUrl) | ✅ |
| `home.html:121–123` | ✅ |
| `chat.html:178–180` | ✅ |
| `my.html:229–231` | ✅ |
| `my.html:262–264` | ✅ |
| `my.html:357–359` | ✅ |
| `my_list.html:93–95` | ✅ |
| `personas.html:576–578` | ✅ |
| `search.html:147–149` | ✅ |
| `world.html:179–181` | ✅ |

※ `chat.html:1062–1063`, `home.html:870–871` — `isLocal` 판정용 (개발 디버그 전용, API URL 결정과 무관)

**`trpg.arcanaverse.ai`가 누락된 분기: 0개**

### 3-3. `/v1/auth/google` 호출 경로

```
my.html line 301:
  fetch(`${API_BASE_URL}/v1/auth/google`, ...)
```

`API_BASE_URL`의 출처: line 229–231 (이번 수정 완료)

`trpg.arcanaverse.ai` 접속 시:
- 수정 전: `http://localhost:8000/v1/auth/google` → ERR_CONNECTION_REFUSED
- 수정 후: `https://api.arcanaverse.ai/v1/auth/google` ✅

### 3-4. `my_list`, `personas`, `search`, `world` API 호출

| 파일 | `trpg`에서 선택되는 API Base |
|------|---------------------------|
| `my_list.html` | `https://api.arcanaverse.ai` ✅ |
| `personas.html` | `https://api.arcanaverse.ai` ✅ |
| `search.html` | `https://api.arcanaverse.ai` ✅ |
| `world.html` | `https://api.arcanaverse.ai` ✅ |

### 3-5. localhost 개발환경 동작 유지

모든 수정 위치에서 조건은 **추가(OR)** 방식이다. `localhost`, `127.0.0.1`, 기타 hostname은 세 가지 조건 중 어느 것도 매칭되지 않으므로 else 분기 `"http://localhost:8000"` 그대로 유지된다.

| hostname | 결과 |
|----------|------|
| `arcanaverse.ai` | `https://api.arcanaverse.ai` ✅ |
| `www.arcanaverse.ai` | `https://api.arcanaverse.ai` ✅ |
| `trpg.arcanaverse.ai` | `https://api.arcanaverse.ai` ✅ |
| `localhost` | `http://localhost:8000` ✅ |
| `127.0.0.1` | `http://localhost:8000` ✅ |
| 기타 | `http://localhost:8000` ✅ |

---

## 4. 누적 수정 현황 (Round 1 + Round 2 합산)

| 파일 | 수정 회차 |
|------|----------|
| `apps/web-html/js/config.js` | Round 1 |
| `apps/web-html/static/js/session.js` | Round 1 |
| `apps/web-html/home.html` | Round 1 |
| `apps/web-html/chat.html` | Round 1 |
| `apps/api/main.py` (CORS) | Round 1 |
| `apps/web-html/my.html` (3곳) | Round 2 |
| `apps/web-html/my_list.html` | Round 2 |
| `apps/web-html/personas.html` | Round 2 |
| `apps/web-html/search.html` | Round 2 |
| `apps/web-html/world.html` | Round 2 |

`apps/web-html` 내 `trpg.arcanaverse.ai` 미처리 분기: **0개**
