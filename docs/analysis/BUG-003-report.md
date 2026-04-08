# BUG-003 Implementation Report

## Ticket ID

- BUG-003

## Summary of Changes

`user_info_v2`가 `www` 서브도메인 범위에만 머물러 `api.arcanaverse.ai` 요청에서 인증 쿠키가 누락되던 문제를 수정했다.

Google 로그인 응답 시 서버가 `user_info_v2` 쿠키를 직접 설정하도록 변경했고, 프로덕션 도메인에서는 쿠키 도메인을 `.arcanaverse.ai`로 지정해 서브도메인 간 공유가 가능하도록 했다.

## Files Modified

- `apps/api/routes/auth_google.py`
  - 로그인 엔드포인트 시그니처에 `Response`, `Request` 추가
  - `response.set_cookie()`로 `user_info_v2` 쿠키 발급 추가
  - 프로덕션 도메인에서:
    - `domain=".arcanaverse.ai"`
    - `samesite="none"`
    - `secure=True`
    - `httponly=True`
  - 로컬/기타 환경 fallback:
    - `domain=None`
    - `samesite="lax"`
    - `secure=False`
- `docs/analysis/BUG-003-report.md`
  - 구현 리포트 추가

## Root Cause Analysis

- 기존 구현은 `user_info_v2`를 JSON 응답 본문으로만 내려주고, 서버가 쿠키 속성(domain/samesite/secure)을 통제하지 않았다.
- 이 상태에서 프론트가 `www.arcanaverse.ai`에서 쿠키를 설정하면 기본적으로 host-only 쿠키가 되어 `api.arcanaverse.ai`로 전송되지 않는다.
- 결과적으로 `credentials: "include"` 호출에서도 API 요청 헤더에 쿠키가 붙지 않아 인증 실패가 발생했다.

## Implementation Details

- 인증 검증 로직(`decode_user_info_token`, `get_current_user_from_token`)은 변경하지 않았다.
- 로그인 시점에만 쿠키 발급을 명확히 추가해, 기존 인증 흐름을 유지하면서 쿠키 스코프 문제를 해결했다.
- 만료 시간은 기존 설정값 `AUTH_USER_INFO_V2_EXPIRE_MINUTES`를 재사용했다.

## Verification Steps

1. Google 로그인 수행
2. DevTools -> Application -> Cookies에서 `user_info_v2` 확인
   - 프로덕션 도메인에서 `Domain=.arcanaverse.ai` 확인
3. 브라우저 콘솔에서 호출
   - `fetch("https://api.arcanaverse.ai/api/my/characters?skip=0&limit=20", { credentials: "include" })`
4. Network 탭에서 요청 Cookie 포함 여부 확인
5. 응답이 200인지 확인
6. 쿠키 삭제 후 재호출 시 401 확인

## Risks / Limitations

- `samesite="none"`은 `secure=True`가 필수이므로 HTTPS 환경 전제가 필요하다.
- 로컬 HTTP 개발 환경에서는 fallback 설정(`secure=False`, `lax`)을 사용하므로 프로덕션과 쿠키 전파 동작이 다를 수 있다.
- 프론트에서 별도로 동일 키(`user_info_v2`)를 다른 속성으로 재설정하면 충돌 가능성이 있다.

## Completion Status

- Implementation Done: YES
- Release Verified: PENDING

## Final Status

- Release Verified: PENDING
- Ticket Done: PENDING

