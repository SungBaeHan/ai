# FEAT-MyList-001 My List 메뉴 구조 구성 (Create / Favorite + 콘텐츠 타입 분리)

---

# Metadata

Type: FEAT  
Severity: major  
Layer: frontend  
Milestone: MS-03

---

# Problem

현재 My List 페이지는 구조가 명확히 정의되어 있지 않음.

Current behavior:

- My List 진입 시 콘텐츠가 단일 리스트 형태로 표시됨
- Create / Favorite 구분 없음
- 콘텐츠 타입(캐릭터/세계관/게임) 구분 없음

Expected behavior:

- 1Depth: My Create | My Favorite 탭 제공
- 2Depth: 각 탭 하위에 콘텐츠 타입 분리
  - 캐릭터 선택
  - 세계관 선택
  - 게임 선택

Impact:

- 콘텐츠 관리 UX 향상
- 사용자 제작 콘텐츠와 소비 콘텐츠 명확히 분리
- 향후 BM/추천/운영 기능 확장 기반 확보

---

# Context

Relevant UI:

- /home → My List 메뉴
- 캐릭터 선택 UI (기존 grid 카드 UI 재사용 가능)

Relevant structure:

- characters
- worlds
- games

Architecture:

Frontend (UI State) → API → MongoDB

---

# Scope

Allowed:

- My List UI 구조 변경
- 탭 UI (Create / Favorite) 추가
- 2Depth 메뉴 구성 (캐릭터 / 세계관 / 게임)
- 기존 카드 컴포넌트 재사용

Not allowed:

- DB schema 변경
- API 구조 변경
- 추천 알고리즘 추가
- 정렬/필터 고도화

---

# Strategy

- 상단에 1Depth 탭 추가
  - My Create
  - My Favorite

- 각 탭 내부에 2Depth 메뉴 구성
  - 캐릭터 선택
  - 세계관 선택
  - 게임 선택

- 콘텐츠 타입별로 리스트 필터링
  - type = character | world | game

- 데이터 기준
  - My Create → owner_id 기준
  - My Favorite → favorite 컬렉션 기준

---

# Acceptance Criteria

1 My List 진입 시 Create / Favorite 탭이 보인다  
2 각 탭에서 콘텐츠 타입 선택 가능  
3 선택된 타입에 맞는 리스트가 정상 출력된다  
4 기존 카드 UI가 깨지지 않는다  
5 기존 기능(캐릭터 선택 등) 정상 동작 유지  

---

# Verification

1 My List 진입  
2 My Create 클릭 → 캐릭터 선택 → 리스트 확인  
3 My Favorite 클릭 → 세계관 선택 → 리스트 확인  
4 각 카드 클릭 시 정상 이동 확인  

---

# Ticket Size Rule

- UI 구조 변경 중심
- 1~3 파일 수정 권장

---

# AI Implementation Instructions

Before coding:

- UI 상태 구조 설계
- 탭 상태 관리 방식 정의

After coding:

- 변경된 파일 목록
- UI 변경 요약
- 테스트 결과
- 영향 범위 설명

---

# Important Rule

1 ticket → 1 branch → 1 PR

---

# Development Principles

- SSOT 기반
- Ticket-driven development
- UI/UX는 점진적 개선