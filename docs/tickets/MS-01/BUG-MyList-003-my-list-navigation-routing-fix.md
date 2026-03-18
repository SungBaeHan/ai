# BUG-MyList-003 My List 메뉴 네비게이션 연결 오류 수정

---

# Metadata

Type: BUG  
Severity: major  
Layer: frontend  
Milestone: MS-03

---

# Problem

상단 `My List` 메뉴를 클릭해도 My List 전용 화면/상태로 진입하지 않고, 실제로는 Home 화면에 그대로 머무르는 문제가 있음.

Current behavior:

- 상단 네비게이션에서 `My List` 클릭 시 전용 My List 화면으로 연결되지 않음
- 결과적으로 Home(`/home.html`)의 기본 콘텐츠(캐릭터/세계관/게임 선택)가 그대로 표시됨
- 로그인 상태에서는 Home 리스트 위에 “준비중입니다.” 또는 “로그인이 필요합니다.” 등의 메시지가 섞여 보일 수 있음
- 비로그인 상태에서도 My List 진입이 아닌 Home 상태처럼 동작함

Expected behavior:

- 상단 `My List` 메뉴 클릭 시 명확하게 My List 전용 화면 또는 My List 전용 상태로 진입해야 함
- Home과 My List는 사용자 관점에서 분리된 메뉴처럼 동작해야 함
- My List 진입 후에는 Home 기본 리스트가 아니라 My List 기준 UI/상태가 보여야 함

Impact:

- 사용자가 메뉴 이동에 실패했다고 인식함
- Home / My List 정보 구조가 무너짐
- 이후 My Create / My Favorite / Empty state UX 검증이 불가능해짐

---

# Context

Relevant files:

- apps/web-html/home.html
- apps/web-html/my.html
- 상단 네비게이션 링크/라우팅 처리 JS
- 관련 상태 초기화 스크립트

Likely root cause:

- `My List` 메뉴 href 또는 click handler가 실제 My List 화면을 가리키지 않음
- 또는 My List 전용 페이지/상태 전환 로직이 연결되지 않음
- 결과적으로 Home이 fallback처럼 동작하고 있음

Architecture note:

- 이 티켓은 frontend navigation / page state 범위에서만 수정
- backend/API 변경 금지

---

# Scope

Allowed:

- `My List` 상단 메뉴 링크 수정
- My List 진입 라우팅 수정
- My List 전용 초기화 진입점 연결
- 필요 시 Home / My List 진입 조건 분리

Not allowed:

- API 수정
- DB schema 변경
- 대규모 라우팅 리팩토링
- My Favorite 데이터 기능 신규 구현
- unrelated UI refactor

---

# Strategy

1. 상단 `My List` 메뉴의 실제 연결 대상 확인
   - href
   - onclick
   - router/state switch

2. My List 진입점 명확화
   - 전용 페이지(`my.html`)가 있으면 그쪽으로 연결
   - 단일 페이지 상태 전환 구조면 My List mode가 확실히 활성화되도록 수정

3. Home / My List 분리
   - Home 기본 콘텐츠와 My List 전용 콘텐츠가 동시에 보이지 않도록 처리
   - My List 진입 시 Home 기본 리스트가 fallback으로 보이지 않게 수정

4. 로그인/비로그인 상태 점검
   - 로그인 여부와 관계없이 `My List` 클릭은 올바른 화면/상태로 이동해야 함
   - 비로그인 시에는 My List 화면 안에서 안내 메시지를 보여주더라도, Home으로 돌아가면 안 됨

---

# Acceptance Criteria

1 `My List` 메뉴 클릭 시 Home이 아닌 My List 전용 화면/상태로 진입한다  
2 My List 진입 후 Home 기본 콘텐츠가 그대로 보이지 않는다  
3 로그인 상태에서 My List 진입 동작이 정상이다  
4 비로그인 상태에서도 My List 진입 자체는 정상이며, 필요 시 My List 내부 안내 메시지가 보인다  
5 Home 메뉴와 My List 메뉴가 서로 명확히 구분되어 동작한다  
6 기존 Home 메뉴 동작은 깨지지 않는다  

---

# Verification

1 `/home.html` 진입 후 상단 `My List` 메뉴 클릭  
2 URL 또는 화면 상태가 실제 My List 진입으로 바뀌는지 확인  
3 Home 기본 리스트가 아니라 My List 전용 UI/상태가 보이는지 확인  
4 로그인 상태에서 동일 동작 확인  
5 비로그인 상태에서 동일 동작 확인  
6 다시 `Home` 메뉴 클릭 시 기존 Home 화면으로 정상 복귀하는지 확인  

---

# Ticket Size Rule

- 1~3 files
- navigation / entrypoint fix only

---

# AI Implementation Instructions

Before coding:

- Find the actual nav link target for `My List`
- Identify whether My List is page-based or state-based
- Explain why the current click ends up in Home

After coding:

- List changed files
- Explain nav fix
- Explain Home/My List separation
- Provide verification result for logged-in and logged-out cases

---

# Important Rule

1 ticket → 1 branch → 1 PR

---

# Development Principles

- SSOT
- Ticket-driven development
- Minimal navigation fix
- Clear UX separation