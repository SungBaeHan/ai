# BUG-002 Implementation Report

## Ticket ID

- BUG-002

## Summary of Changes

`/api/my/characters`, `/api/my-create/characters`가 브라우저 `credentials: "include"` 호출에서 `401 Missing token`이 발생하던 문제를 수정했다.

원인은 인증 토큰 추출기에서 `user_info_v2` 쿠키를 토큰 소스로 인식하지 않던 점이었고, 쿠키 소스 목록에 `user_info_v2`를 추가해 쿠키 기반 인증 흐름을 복구했다.

## Files Modified

- `apps/api/utils/auth_token.py`
  - 토큰 추출 소스에 `user_info_v2` 쿠키 추가
  - 토큰 소스 디버그 로그 필드에 `cookie_user_info_v2` 추가
  - 쿠키 소스 라벨 분기(`cookie_user_info_v2`) 추가

## Root Cause Analysis

- My Create API 자체는 `get_current_user_from_token`을 사용하고 있었고, 이 의존성은 헤더/쿠키에서 토큰을 찾기 위해 `extract_token()`을 호출한다.
- 하지만 `extract_token()`의 쿠키 탐색 대상이 `access_token`, `token`, `session`으로 제한되어 있어서, 실제 로그인 흐름에서 사용되는 `user_info_v2` 쿠키를 읽지 못했다.
- 결과적으로 브라우저에서 `credentials: "include"`만 전달하면 토큰 미탐지로 `401 Missing token`이 반환되었다.

## Implementation Details

- 인증 방식 변경이 아닌 **기존 인증 로직 보완**으로 구현했다.
- 헤더 기반 우선순위는 유지하고, 쿠키 후보에 `user_info_v2`만 추가했다.
- `get_current_user_from_token`/`decode_user_info_token` 흐름은 변경하지 않아 회귀 위험을 최소화했다.

## Verification Steps

1. 로그인 후 브라우저에 `user_info_v2` 쿠키가 존재하는지 확인
2. Authorization 헤더 없이 아래 호출
   - `GET /api/my/characters?skip=0&limit=20` (`credentials: "include"`)
   - `GET /api/my-create/characters?skip=0&limit=20` (`credentials: "include"`)
3. 응답이 `200`이며 사용자 본인 creator 문서만 반환되는지 확인
4. 쿠키 삭제 후 동일 호출 시 `401` 반환 확인
5. 비정상 토큰(user_id 파싱 불가) 시 안전하게 오류 처리되는지 확인

## Risks / Limitations

- 본 수정은 토큰 소스 인식 버그를 해결하는 범위로 제한되어 있으며, 인증/세션 정책 자체(만료, 무효화, 권한 정책)는 변경하지 않았다.
- 브라우저 환경에서 `SameSite`/`Secure`/도메인 설정이 잘못된 경우에는 여전히 쿠키가 서버로 전달되지 않을 수 있다(애플리케이션 코드 외 설정 이슈).

## Completion Status

- Implementation Done: YES
- Release Verified: PENDING

## Final Status

- Release Verified: PENDING
- Ticket Done: PENDING

