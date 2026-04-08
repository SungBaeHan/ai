# Ticket Title

BUG-002 My Create Character List API Cookie Auth Fix

---

# Metadata

Type: BUG
Severity: major
Layer: api
Milestone: MS-01

---

# Problem

FEAT-001 구현 이후 My List / My Create 전용 API는 추가되었지만, 인증 방식이 티켓 요구사항과 다르게 구현되었다.

Current behavior:

* `/api/my/characters`, `/api/my-create/characters`는 Swagger에 정상 노출됨
* Authorization Bearer 헤더를 넣으면 정상 동작
* 하지만 브라우저에서 쿠키 기반 호출 시 인증 실패 발생

브라우저 호출 예:

fetch("https://api.arcanaverse.ai/api/my/characters?skip=0&limit=20", {
credentials: "include"
})

응답:

* 401 Unauthorized
* {"detail":"Missing token"}

Expected behavior:

* 해당 API는 user_info_v2 쿠키 기반 인증으로 동작해야 함
* credentials: "include" 만으로 정상 호출되어야 함
* 서버는 user_info_v2에서 user_id를 추출해야 함
* creator == current_user._id 조건으로 조회해야 함

Impact:

* 프론트에서 정상 호출 불가능
* 로그인 구조와 충돌
* 티켓 요구사항 불일치

---

# Context

이번 작업은 신규 기능이 아니라 인증 방식 수정이다.

현재 상태:

* API 존재

  * GET /api/my/characters
  * GET /api/my-create/characters
* Swagger 노출됨
* 현재 인증: Bearer 기반
* 요구사항: 쿠키 기반

Relevant files:

* apps/api/routes/my_create.py
* apps/api/deps/auth.py
* user_info_v2 관련 auth 로직

Relevant data:

* users._id → ObjectId
* characters.creator → ObjectId

Architecture rule:

* API Route → Usecase → Adapter
* 최소 수정 원칙 적용

---

# Scope

Allowed:

* my_create 라우터 인증 방식 수정
* user_info_v2 로직 재사용
* 쿠키 기반 인증 연결
* 예외 처리 정리

Not allowed:

* DB 변경
* 인프라 변경
* OAuth 구조 변경
* 프론트 수정

---

# Strategy

1. get_current_user_from_token 사용 위치 확인
2. user_info_v2 해석 로직 재사용
3. Authorization 헤더 의존 제거
4. request.cookies에서 user_info_v2 읽기
5. user_id → ObjectId 변환
6. creator 조건으로 조회
7. 401 / 400 예외 처리

목표:

* Bearer 없이 동작
* 브라우저 호출 정상화

---

# Acceptance Criteria

1. /api/my/characters 정상 동작
2. /api/my-create/characters 정상 동작
3. credentials: include 호출 시 200
4. Authorization 없이 동작
5. creator 기준 조회 유지
6. 쿠키 없으면 401
7. user_id 오류 시 400
8. 응답 구조 유지
9. 기존 기능 영향 없음

---

# Verification

1. 서버 실행
2. 로그인 수행
3. 쿠키 생성 확인
4. 브라우저에서 호출

fetch("https://api.arcanaverse.ai/api/my/characters?skip=0&limit=20", {
credentials: "include"
})

5. 200 + 데이터 확인
6. 다른 계정 비교
7. 쿠키 제거 후 401 확인

---

# Ticket Size Rule

* 1~3 파일 수정
* 단일 변경

---

# AI Implementation Instructions

Before coding:

* root cause 분석
* 수정 파일 정의
* 구현 계획

After coding:

* 변경 파일
* 변경 요약
* 검증 방법
* 리스크

추가:

* Bearer → 쿠키 변경 이유 설명
* 인증 방식 변경 내용
* 브라우저 테스트 결과

---

# Important Rule

1 ticket → 1 branch → 1 PR

---

# Development Principles

* SSOT
* Architecture-first
* Ticket-driven
* AI-assisted
