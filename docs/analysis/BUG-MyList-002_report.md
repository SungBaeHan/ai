# BUG-MyList-002 My List 초기화 범위 오류 및 Empty State 통일 — Implementation Report

**Ticket:** `docs/tickets/MS-01/BUG-MyList-002-my-list-scope-and-empty-state-fix.md`  
**Date:** 2025-02-27  

---

## Completion Status

- Implementation Done: **YES**
- Release Verified: **PENDING**

---

## Root Cause

이전 변경에서 `My List` UI/초기화 로직이 `apps/web-html/home.html`에 포함되면서:

- Home(`/home.html`) 진입 시에도 My List 관련 로직이 실행되고
- `/v1/characters/my` 같은 “내 콘텐츠” API가 Home에서 호출되며
- 인증/컨텍스트 부족 시 HTTP 400/401 등의 오류가 사용자에게 노출될 수 있는 상태가 되었습니다.

또한 “데이터 없음”/에러 메시지가 화면마다 다르게 표현되어 UX가 불안정했습니다.

---

## Files Changed

- `apps/web-html/home.html`

---

## Fix Summary

### 1) Page/Scope Guard (Home에서 My List 로직 제거)

- `home.html`에서 My List(1Depth Create/Favorite) UI 및 관련 상태/핸들러를 제거했습니다.
- 따라서 Home에서는 기존 콘텐츠(캐릭터/세계관/게임 선택)만 정상 동작합니다.

### 2) API Guard (Home에서 `/my` API 호출 제거)

- `home.html`의 캐릭터 로딩을 다시 `GET /v1/characters`로 되돌렸습니다.
- 결과적으로 Home에서 `/v1/characters/my` 호출이 발생하지 않습니다.

### 3) Empty State 통일 + 중앙 정렬

- 데이터가 없거나(빈 리스트) 로딩 실패(HTTP 에러 포함) 시 사용자에게 에러를 그대로 보여주지 않고,
  아래 메시지를 카드 영역 중앙 정렬로 통일해 표시하도록 했습니다.

```txt
결과 없음
표시할 항목이 없습니다.
```

---

## Verification Steps (Ticket 기준)

1. `/home.html` 진입 → 기존 리스트(캐릭터/세계관/게임 선택) 정상 출력 확인
2. 브라우저 네트워크 탭에서 `/v1/characters/my` 호출이 **없음** 확인
3. 데이터가 없거나(검색 결과 0건 등) API 실패 시, 아래 메시지가 중앙 정렬로 표시되는지 확인
   - `결과 없음`
   - `표시할 항목이 없습니다.`
4. 콘솔/네트워크 에러가 사용자 UI에 그대로 노출되지 않는지 확인
5. 기존 카드 UI 및 카드 클릭 이동 동작이 유지되는지 확인

---

## Risks / Limitations

- 본 티켓은 “Home에서 My List 로직이 실행되는 문제”를 제거하는 것이 핵심이며,
  My List 전용 페이지 분리/신규 기능 추가는 스코프 밖(구조 리팩토링/새 기능)이라 수행하지 않았습니다.
- Release Verified는 Oracle VM 배포 환경에서 실제 브라우저로 확인이 필요합니다.

