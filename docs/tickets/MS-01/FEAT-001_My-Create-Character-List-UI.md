# FEAT-001 My Create Character List UI

Home 화면 패턴을 재사용해 My Create 전용 캐릭터 목록을 노출한다.

---

# Metadata

Type: FEAT  
Severity: major  
Layer: adapter  
Milestone: MS-01

---

# Problem

현재 백엔드에는 아래 API가 준비되어 있다.

- GET `/api/my/characters`
- GET `/api/my-create/characters`

또한 MongoDB 컬렉션에는 생성자 식별용으로 `creator: ObjectId('692695d274f310fbaa14ccc5')` 형태의 데이터가 저장되어 있으며,  
프론트는 로컬 쿠키 `user_info_v2` 를 읽어 현재 로그인 사용자를 식별한 뒤 My Create API 를 호출해야 한다.

Current behavior:

- Home 화면처럼 “내가 만든 캐릭터 목록”을 보여주는 전용 UI 가 없다
- 프론트에서 `user_info_v2` 쿠키 기반으로 My Create API 를 호출하지 않는다
- 사용자는 자신이 만든 캐릭터를 별도 화면에서 확인할 수 없다

Expected behavior:

- 프론트가 로컬 쿠키 `user_info_v2` 를 읽는다
- 사용자 식별값을 기반으로 GET `/api/my-create/characters` 를 호출한다
- Home 화면의 캐릭터 목록 UI 패턴을 재사용해 “내가 만든 캐릭터 목록”을 렌더링한다
- 빈 목록일 경우 empty state 를 보여준다

Impact:

- 사용자가 자신이 생성한 캐릭터를 확인하는 핵심 UX 가 비어 있음
- My List 와 My Create 의 개념 분리가 UI 에 반영되지 않음
- 라이브 데모 및 티켓 기반 개발 흐름 시연 시 사용자 가치가 드러나지 않음

---

# Context

Relevant API:

- GET `/api/my/characters`
- GET `/api/my-create/characters`

Relevant data condition:

- MongoDB document has `creator: ObjectId(...)`
- Current example creator value:
  `692695d274f310fbaa14ccc5`

Frontend requirement:

- local cookie `user_info_v2` 를 읽어서 사용자 정보를 확보
- 해당 사용자 기준으로 My Create API 호출
- Home 화면처럼 캐릭터 카드 목록 UI 재사용

Possible relevant files:

- frontend home page character list rendering component
- my list / character list related api client
- cookie utility or auth utility
- my create page or tab component

Architecture hint:

- UI 는 기존 Home 캐릭터 목록 컴포넌트/패턴을 최대한 재사용
- 인증/사용자 식별은 프론트에서 `user_info_v2` 해석 후 API 호출 흐름에 맞춤
- 불필요한 백엔드 변경 없이 프론트 연결만 수행

---

# Scope

Allowed:

- My Create 화면 또는 섹션 UI 추가
- `user_info_v2` 쿠키 읽기 로직 연결
- GET `/api/my-create/characters` 호출 로직 추가
- Home 화면 캐릭터 목록 UI 재사용 또는 소규모 공통화
- loading / empty / error 상태 처리
- 필요한 범위 내의 프론트 API 클라이언트 수정

Not allowed:

- DB schema 변경
- 백엔드 API 스펙 변경
- 인증 체계 전면 수정
- unrelated refactor
- Home 전체 구조 대규모 개편
- My List 와 My Create 를 한 티켓에서 동시에 재설계

---

# Strategy

Example approaches:

- 기존 Home 화면에서 캐릭터 목록을 그리는 컴포넌트나 렌더링 패턴을 식별
- 공통 캐릭터 리스트 UI 가 가능하면 최소 범위로 추출
- `user_info_v2` 쿠키에서 현재 사용자 정보 파싱
- My Create 전용 API client function 추가
- 페이지/탭 진입 시 API 호출 후 결과 렌더링
- 결과가 없으면 “아직 만든 캐릭터가 없습니다” 형태의 empty state 제공

Implementation notes:

- 쿠키 파싱 실패 시 graceful fallback 처리
- API 실패 시 사용자에게 기본 에러 상태 표시
- 카드 클릭 시 기존 캐릭터 상세 이동 패턴이 있다면 그대로 유지
- 스타일은 Home 화면과 시각적으로 일관되게 유지

---

# Acceptance Criteria

1. My Create 화면 또는 섹션에서 GET `/api/my-create/characters` 호출이 수행된다

2. 프론트는 로컬 쿠키 `user_info_v2` 를 읽는 흐름으로 동작한다

3. 응답 데이터를 Home 화면과 유사한 캐릭터 카드 목록 형태로 렌더링한다

4. 목록이 비어 있을 때 empty state 가 표시된다

5. 로딩 중에는 loading state 가 표시된다

6. API 호출 실패 시 error state 또는 사용자 안내가 표시된다

7. 기존 Home 화면 캐릭터 목록 동작은 깨지지 않는다

---

# Verification

1. 프론트 실행

2. 브라우저 Application / Storage 에서 `user_info_v2` 쿠키 존재 확인

3. My Create 화면 또는 해당 메뉴로 이동

4. Network 탭에서 GET `/api/my-create/characters` 호출 확인

5. 응답 데이터가 있을 경우 캐릭터 카드 목록이 Home 화면과 유사하게 표시되는지 확인

6. 응답이 빈 배열일 경우 empty state 표시 확인

7. 쿠키 제거 또는 비정상 값 설정 시 fallback / 에러 처리 확인

8. 기존 Home 화면 캐릭터 목록이 정상 동작하는지 회귀 확인

---

# Ticket Size Rule

Tickets should remain **small and focused**.

This ticket should typically modify:

- My Create page/tab component
- API client or fetch layer
- cookie/auth utility or shared list component

Do not expand into My List UI or global navigation redesign in this ticket.

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

Specific review points:

- `user_info_v2` 쿠키 구조를 어떻게 읽는지
- 어떤 사용자 식별값으로 API 호출을 연결했는지
- Home 화면 UI 재사용 범위가 어디까지인지
- 기존 목록 UI 와 충돌 가능성은 없는지

---

# Important Rule

One ticket should produce:

1 branch  
1 pull request

Suggested branch name:

`feat/my-create-character-list-ui`

---

# Development Principles

Arcanaverse follows **AI-native development**.

Principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation
- Reuse existing UI patterns first
- Keep frontend changes minimal and demonstrable