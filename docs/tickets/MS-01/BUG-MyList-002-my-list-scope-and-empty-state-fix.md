# BUG-MyList-002 My List 초기화 범위 오류 및 Empty State 통일

---

# Metadata

Type: BUG  
Severity: major  
Layer: frontend  
Milestone: MS-03

---

# Problem

My List UI 및 로직이 Home 화면에서도 실행되며, API 호출 오류(HTTP 400)가 사용자에게 그대로 노출됨.

Current behavior:

- Home(`/home.html`) 진입 시 My List UI가 함께 렌더링됨
- `/v1/characters/my` API가 Home에서도 호출됨
- 인증/컨텍스트 부족으로 HTTP 400 발생
- 에러 메시지가 그대로 화면에 출력됨
- Empty 상태 메시지가 화면마다 다르게 표시됨

Expected behavior:

- Home에서는 기존 콘텐츠만 정상 출력
- My List 로직은 My List 페이지에서만 실행
- 데이터가 없을 경우 아래 메시지로 통일:

결과 없음  
표시할 항목이 없습니다.

- 해당 메시지는 화면 중앙에 정렬

Impact:

- UX 혼란 (버그처럼 보임)
- API 불필요 호출 발생
- 페이지 구조 분리 실패

---

# Context

Relevant files:

- apps/web-html/home.html
- apps/web-html/my.html (또는 My List UI 포함 파일)
- 관련 JS (initMyList, loadCharacters 등)

Key issue:

- My List 초기화 로직이 페이지 구분 없이 실행됨

---

# Scope

Allowed:

- My List 초기화 조건 분리 (page guard)
- Empty state UI 통일
- HTTP 에러 메시지 제거 또는 대체
- 최소한의 JS 조건 분기 추가

Not allowed:

- API 수정
- DB 변경
- 구조 리팩토링
- 새로운 기능 추가

---

# Strategy

1. Page Guard 추가

- My List 관련 로직은 특정 DOM 존재 시에만 실행
- 예:
  - `#my-list-root` 또는 My List 전용 컨테이너 기준

2. API Guard 추가

- user context 없을 경우 `/my` API 호출 금지

3. Empty State 통일

모든 “데이터 없음” 상태에서 아래 메시지 사용:

결과 없음  
표시할 항목이 없습니다.

4. UI 정렬

- Empty 메시지는 중앙 정렬
- 기존 카드 영역 내에서 자연스럽게 표시

5. 에러 처리

- HTTP 400 등 에러는 사용자에게 노출하지 않고 empty state로 처리

---

# Acceptance Criteria

1 Home 진입 시 My List UI가 보이지 않는다  
2 Home에서 `/my` API 호출이 발생하지 않는다  
3 My List에서 데이터 없을 경우 메시지가 통일된다  
4 메시지가 중앙 정렬로 표시된다  
5 HTTP 에러 메시지가 사용자에게 노출되지 않는다  
6 기존 카드 UI 및 기능이 깨지지 않는다  

---

# Verification

1 `/home.html` 진입 → 정상 리스트 출력 확인  
2 네트워크 탭에서 `/my` API 호출 없음 확인  
3 My List 진입 → My Favorite → 캐릭터 선택  
4 데이터 없을 경우 아래 메시지 확인:

결과 없음  
표시할 항목이 없습니다.

5 메시지가 중앙 정렬인지 확인  
6 콘솔/네트워크 에러 노출 여부 확인  

---

# Ticket Size Rule

- 1~3 파일 수정
- 조건 분기 + UI 메시지 통일

---

# AI Implementation Instructions

Before coding:

- My List 초기화 위치 확인
- 실행 조건 분석

After coding:

- 변경 파일 목록
- 수정된 조건 로직 설명
- Empty state 처리 방식 설명
- 검증 결과

---

# Important Rule

1 ticket → 1 branch → 1 PR

---

# Development Principles

- SSOT
- Minimal change
- UX consistency
- Ticket-driven development