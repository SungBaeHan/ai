# Ticket Title

BUG-003 User Info Cookie Domain Fix for Cross-Subdomain Auth

---

# Metadata

Type: BUG
Severity: major
Layer: api
Milestone: MS-01

---

# Problem

현재 로그인 이후 발급되는 `user_info_v2` 쿠키가 `www.arcanaverse.ai` 도메인에만 적용되어, API 도메인(`api.arcanaverse.ai`) 요청 시 쿠키가 전달되지 않는 문제가 발생한다.

Current behavior:

* 로그인 후 `user_info_v2` 쿠키는 정상 생성됨
* 브라우저에서 `https://www.arcanaverse.ai` 기준으로는 쿠키 확인 가능
* 하지만 아래 API 호출 시 쿠키가 포함되지 않음

https://api.arcanaverse.ai/api/my/characters

* 결과:

  * 401 Unauthorized
  * {"detail":"Missing token"}

Expected behavior:

* `user_info_v2` 쿠키가 모든 서브도메인에서 공유되어야 함
* `api.arcanaverse.ai` 요청에도 쿠키가 자동 포함되어야 함
* 브라우저 fetch 호출 시 credentials: include 만으로 인증이 정상 동작해야 함

Impact:

* 브라우저 기반 API 호출이 실패함
* 프론트엔드에서 My List / My Create 기능 연결 불가능
* 쿠키 기반 인증 구조가 실제 동작하지 않음

---

# Context

현재 시스템은 Google OAuth 로그인 후 `user_info_v2` 쿠키를 기반으로 사용자 인증을 수행한다.

문제의 원인은 쿠키 발급 시 domain 설정이 특정 서브도메인(`www.arcanaverse.ai`)으로 제한되어 있기 때문이다.

Relevant files:

* 로그인 처리 코드 (Google OAuth route)
* `create_user_info_token` 또는 `set_cookie` 호출 위치
* `apps/api/routes/auth_*.py`
* `apps/api/utils/auth_token.py`

Relevant config:

* Cookie domain 설정
* SameSite / Secure 옵션

Architecture rule:

* 인증 로직 변경 없이 쿠키 설정만 수정
* 기존 인증 흐름 유지

---

# Scope

Allowed:

* user_info_v2 쿠키 발급 시 domain 설정 수정
* SameSite / Secure 옵션 보완
* 쿠키 범위를 전체 서브도메인으로 확장

Not allowed:

* 인증 로직 변경
* DB 변경
* API 구조 변경
* OAuth 흐름 수정
* 프론트엔드 수정

---

# Strategy

1. `user_info_v2` 쿠키를 발급하는 위치를 찾는다
2. set_cookie 호출 시 domain 값을 수정한다
3. domain을 ".arcanaverse.ai"로 설정하여 모든 서브도메인에서 접근 가능하게 한다
4. SameSite와 Secure 옵션을 cross-domain 환경에 맞게 설정한다

수정 방향:

* 기존 domain 제거 또는 변경
* domain=".arcanaverse.ai" 적용
* samesite="None"
* secure=True 유지

---

# Acceptance Criteria

1. 로그인 후 user_info_v2 쿠키가 ".arcanaverse.ai" 도메인으로 설정된다
2. 브라우저에서 api.arcanaverse.ai 요청 시 쿠키가 자동 포함된다
3. 아래 fetch 호출이 정상 동작한다

fetch("https://api.arcanaverse.ai/api/my/characters?skip=0&limit=20", {
credentials: "include"
})

4. Authorization 헤더 없이도 200 응답 반환
5. 쿠키 제거 시 401 정상 반환
6. 기존 로그인 및 인증 로직에 영향 없음

---

# Verification

1. 서버 실행
2. 로그인 수행
3. DevTools → Application → Cookies 확인

   * Domain이 ".arcanaverse.ai"인지 확인
4. 브라우저 콘솔에서 API 호출
5. Network 탭에서 요청 확인

   * Cookie 포함 여부 확인
6. 응답이 200인지 확인
7. 쿠키 삭제 후 재호출 → 401 확인

---

# Ticket Size Rule

* 1~2 파일 수정
* 단일 설정 변경

---

# AI Implementation Instructions

Before coding:

* root cause: 쿠키 domain 설정 문제 확인
* 수정 위치: set_cookie 호출 지점
* 구현 방법: domain 옵션 수정

After coding:

* 변경 파일 목록
* 변경된 쿠키 설정
* 브라우저 테스트 결과
* 리스크 (SameSite / Secure 관련)

---

# Important Rule

1 branch
1 pull request

---

# Development Principles

* SSOT
* Architecture-first
* Ticket-driven
* AI-assisted
