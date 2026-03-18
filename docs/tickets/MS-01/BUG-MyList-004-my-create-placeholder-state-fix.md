# BUG-MyList-004 My Create 데이터 호출 제거 및 Placeholder 상태 통일

---

# Metadata

Type: BUG  
Severity: major  
Layer: frontend  
Milestone: MS-03

---

# Problem

현재 `My List`의 `My Create` 영역은 아직 실제 데이터 연동 범위가 아닌데, 탭별로 서로 다른 데이터 호출/출력 동작이 발생하고 있음.

Current behavior:

- `My Create > 캐릭터 선택`에서 `/v1/characters/my` 호출이 발생하며 HTTP 400 에러가 남
- `My Create > 세계관 선택`에서는 실제 데이터가 로드됨
- `My Create > 게임 선택`에서는 실제 데이터가 로드됨
- 즉, `My Create` 내부 동작이 탭별로 불일치함

Expected behavior:

- 현재 단계에서는 `My Create`는 **메뉴/화면 구조만 제공하는 placeholder 상태**여야 함
- `캐릭터 선택 / 세계관 선택 / 게임 선택` 모두 실제 데이터 호출 없이 동일한 empty state만 표시해야 함

표시 문구:

결과 없음  
표시할 항목이 없습니다.

Impact:

- 현재 티켓 스코프(메뉴 오픈 전용)와 실제 동작이 불일치함
- 일부 탭에서 실제 데이터가 노출되어 UX와 개발 상태를 혼동시킴
- 불필요한 API 호출 및 400 에러가 발생함

---

# Context

Relevant files:

- apps/web-html/my_list.html
- My List 관련 JS 로딩 함수
- 캐릭터/세계관/게임 탭 전환 핸들러

Likely root cause:

- `My Create` 모드에서 탭별 데이터 로더가 완전히 비활성화되지 않음
- 캐릭터는 `/characters/my` 호출 코드가 남아 있고
- 세계관/게임은 기존 데이터 로드 분기가 그대로 살아 있음

Current intended scope:

- My List 메뉴 진입 / 화면 분리
- 1Depth / 2Depth UI 구조 제공
- 데이터 연동은 후속 티켓에서 구현

---

# Scope

Allowed:

- `My Create` 모드에서 데이터 호출 제거
- 캐릭터/세계관/게임 탭 모두 empty state로 통일
- 불필요한 API 호출 제거
- 에러 UI/콘솔 발생 원인 분기 제거

Not allowed:

- API 수정
- DB schema 변경
- My Create 실제 데이터 기능 구현
- Favorite 기능 구현
- 대규모 리팩토링

---

# Strategy

1. `My Create` 모드 진입 시 데이터 로더 비활성화
   - 캐릭터/세계관/게임 모두 실제 API 호출 금지

2. 탭별 UI 통일
   - 세 탭 모두 아래 메시지를 중앙 정렬로 표시

결과 없음  
표시할 항목이 없습니다.

3. 캐릭터 탭의 `/v1/characters/my` 호출 제거
4. 세계관/게임 탭의 실제 데이터 렌더 제거
5. 현재 단계에서는 `My Create`를 placeholder UI로 고정

---

# Acceptance Criteria

1 `My Create > 캐릭터 선택`에서 API 호출이 발생하지 않는다  
2 `My Create > 세계관 선택`에서 API 호출이 발생하지 않는다  
3 `My Create > 게임 선택`에서 API 호출이 발생하지 않는다  
4 세 탭 모두 동일한 empty state가 표시된다  
5 HTTP 400 에러가 발생하지 않는다  
6 현재 `My List` 메뉴/탭 구조는 유지된다  

---

# Verification

1 `/my_list.html` 진입
2 `My Create > 캐릭터 선택` 클릭
3 네트워크 탭에서 관련 데이터 API 호출 없음 확인
4 아래 문구 표시 확인

결과 없음  
표시할 항목이 없습니다.

5 `My Create > 세계관 선택` 클릭 후 동일 확인
6 `My Create > 게임 선택` 클릭 후 동일 확인
7 콘솔에 400 에러가 남지 않는지 확인

---

# Ticket Size Rule

- 1~3 files
- frontend conditional cleanup only

---

# AI Implementation Instructions

Before coding:

- Identify all data-loading branches executed under `My Create`
- Explain why character/world/game currently behave differently

After coding:

- List changed files
- Explain removed API calls
- Explain how placeholder mode is enforced
- Provide verification result for all three tabs

---

# Important Rule

1 ticket → 1 branch → 1 PR

---

# Development Principles

- SSOT
- Ticket-driven development
- Minimal change
- Placeholder-first implementation