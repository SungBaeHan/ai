# Ticket Title

FEAT-001 My Create Character List API

---

# Metadata

Type: FEAT
Severity: major
Layer: api
Milestone: MS-01

---

# Problem

현재 Character 문서에는 아래와 같이 creator 필드가 포함되어 있다.

- `creator: ObjectId('692695d274f310fbaa14ccc5')`

그리고 users 컬렉션은 아래 구조를 가진다.

- `_id: ObjectId('692695d274f310fbaa14ccc5')`
- `google_id: "113602532019760492929"`

현재 Google OAuth Login 이후 서버는 `user_info_v2` 쿠키를 생성하고 있다.

예시:

- `user_id=str(user_doc["_id"])`
- `email=user_doc["email"]`
- `display_name=...`
- `member_level=...`
- `last_login_at=...`

하지만 My List / My Create 화면에서 현재 로그인한 사용자가 직접 생성한 Character 목록을 조회하는 전용 API가 없다.

Current behavior:

- 로그인은 Google OAuth 기반으로 처리된다.
- 서버는 로그인 후 `user_info_v2` 쿠키를 발급한다.
- Character 문서에는 creator(ObjectId)가 저장되어 있다.
- 하지만 현재 로그인 사용자 기준으로 creator가 일치하는 Character 목록을 반환하는 API가 없다.

Expected behavior:

- `My List` 또는 `My Create` 계열 API 그룹 아래에
  현재 로그인 사용자의 Character 목록을 조회하는 API가 추가되어야 한다.
- 클라이언트는 로컬 쿠키 `user_info_v2`를 서버로 전달한다.
- 서버는 `user_info_v2`를 해석해 `user_id`를 얻는다.
- 해당 `user_id`와 일치하는 users._id / character.creator 기준으로
  현재 사용자가 생성한 Character 목록을 반환한다.

Impact:

- My List / My Create UI에서 사용자 생성 캐릭터를 정상적으로 노출할 수 없다.
- 현재는 프론트가 사용자별 캐릭터 목록을 안정적으로 조회할 수 있는 서버 API가 없다.
- 이후 즐겨찾기, 소유 목록, 생성 목록 기능 확장 시 기준 API가 부족하다.

---

# Context

현재 로그인 구조는 Google OAuth 기반이다.

서버 흐름 예시:

1. Google 토큰 검증
   - `user_info = verify_google_token(body.token)`

2. users 컬렉션 동기화
   - `user_doc = get_or_create_user(user_info)`

3. 로그인 후 `user_info_v2` 쿠키 생성
   - `create_user_info_token(...)`

이 쿠키에는 최소한 다음과 같은 정보가 들어간다.

- user_id
- email
- display_name
- member_level
- last_login_at

이번 티켓에서는 이 쿠키를 서버에서 해석해 현재 사용자 식별값을 확보하고,
그 값을 기반으로 Character.creator 와 매칭되는 목록 조회 API를 추가하면 된다.

Relevant modules:

- Google OAuth login route / auth route
- `create_user_info_token(...)` 생성 로직
- `user_info_v2` 해석 로직
- Character 조회 route
- Character usecase / service
- MongoDB character adapter / repository

Relevant data:

- users._id = ObjectId
- characters.creator = ObjectId

Architecture rule:

- API Route → Usecase → Adapter
- 가능하면 route에서 직접 Mongo 접근하지 말고 기존 구조를 따른다.

Suggested API direction:

- Swagger 그룹: `My List` 또는 `My Create`
- 예시 엔드포인트:
  - `GET /api/my/characters`
  - 또는 `GET /api/my-create/characters`

Response direction:

- 최소한 Character 목록을 프론트에서 선택 UI에 사용할 수 있는 수준으로 반환
- 상세 스펙은 기존 Character list 응답 형식을 최대한 재사용

---

# Scope

Allowed:

- 현재 로그인 유저 기준 Character 목록 조회 API 추가
- `user_info_v2`를 서버에서 해석하는 처리 추가 또는 기존 로직 재사용
- `user_id`를 ObjectId로 변환하여 creator 기준 조회 로직 추가
- Swagger `/docs` 에 API 노출
- 기존 Character 응답 스키마 재사용 또는 최소 범위 내 DTO 추가

Not allowed:

- database schema changes
- infrastructure changes
- unrelated refactors
- large architecture modifications
- OAuth 로그인 전체 구조 변경
- 쿠키 발급 포맷 변경

---

# Strategy

추천 접근 방식:

1. 인증/쿠키 해석 로직 재사용
   - 기존 `user_info_v2` 해석 방식이 있으면 재사용
   - 없으면 최소 범위의 helper/usecase 추가

2. 현재 사용자 식별
   - `user_info_v2`에서 `user_id` 추출
   - `user_id`를 Mongo ObjectId로 변환

3. Character 목록 조회
   - `creator == current_user_object_id` 조건으로 조회
   - 필요 시 정렬 기준은 최근 생성순 또는 기존 list 기준 재사용

4. API 계층 분리
   - Route 에서는 쿠키/요청 처리
   - Usecase 에서는 현재 유저 기준 캐릭터 조회
   - Adapter 에서는 Mongo 조회 수행

5. 응답 최소화
   - My Create 캐릭터 선택 UI에 필요한 필드만 반환하거나
   - 기존 캐릭터 목록 응답 구조를 재사용

구현 힌트:

- 쿠키 기반 인증이므로 요청에서 `user_info_v2`를 안정적으로 읽어야 한다.
- `user_id`는 문자열일 가능성이 높으므로 ObjectId 변환 예외 처리가 필요하다.
- 인증 실패 / 쿠키 없음 / 잘못된 토큰 / 잘못된 ObjectId 는 명확한 에러로 반환해야 한다.

---

# Acceptance Criteria

1. 로그인 상태에서 `user_info_v2` 쿠키를 포함해 API 호출 시,
   현재 로그인 사용자가 생성한 Character 목록이 반환된다.

2. 조회 조건은 `character.creator == current_user._id` 기준으로 동작한다.

3. 쿠키가 없거나 유효하지 않으면 인증 실패 응답을 반환한다.

4. 잘못된 `user_id` 형식 등 ObjectId 변환 실패 시 안전하게 에러 처리된다.

5. API가 Swagger(`/docs`)에 노출된다.

6. 기존 로그인/캐릭터 관련 기능에는 회귀가 없어야 한다.

---

# Verification

1. API 서버 실행
2. Google OAuth 로그인 수행
3. 브라우저에 `user_info_v2` 쿠키가 생성되었는지 확인
4. Swagger 또는 브라우저/프론트에서 대상 API 호출
5. 현재 로그인 사용자와 creator가 일치하는 Character 목록이 반환되는지 확인
6. 다른 사용자 계정으로 로그인 후 다른 목록이 반환되는지 확인
7. 쿠키 제거 후 다시 호출하여 인증 실패 응답 확인
8. 잘못된 쿠키/비정상 user_id 상황을 만들어 예외 처리 확인

---

# Ticket Size Rule

Tickets should remain **small and focused**.

A single ticket should typically modify:

- 1–3 files
- a single logical change

Large refactors should be split into multiple tickets.

---

# AI Implementation Instructions

Before coding the AI must provide:

- root cause analysis
- files to modify
- implementation plan

After coding the AI must provide:

- files changed
- summary of changes
- verification steps
- potential risks

---

# Important Rule

One ticket should produce:

1 branch
1 pull request

---

# Development Principles

Arcanaverse follows **AI-native development**.

Principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation