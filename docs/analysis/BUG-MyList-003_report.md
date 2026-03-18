# BUG-MyList-003 My List 메뉴 네비게이션 연결 오류 수정 — Implementation Report

**Ticket:** `docs/tickets/MS-01/BUG-MyList-003-my-list-navigation-routing-fix.md`  
**Date:** 2025-02-27  

---

## Completion Status

- Implementation Done: **YES**
- Release Verified: **PENDING**

---

## Root Cause

`My List` 메뉴가 실제로는 전용 화면으로 라우팅되지 않고, `home.html` 내부 클릭 핸들러에서 로그인 체크/토스트 처리만 수행되어 결과적으로 Home 화면에 머무르는 형태였습니다.

또한 `my.html`의 상단 네비게이션에서도 `My List`가 `/home.html`로 연결되어 있어 Home/My List가 구분되지 않았습니다.

---

## Files Changed

- `apps/web-html/home.html`
- `apps/web-html/my.html`
- `apps/web-html/my_list.html` (신규)

---

## Fix Summary

### 1) My List 진입점 명확화 (전용 페이지 추가)

- `apps/web-html/my_list.html`을 추가해 **My List 전용 화면**을 제공합니다.
- Home과 분리된 URL/화면 상태로 진입하므로, 사용자 관점에서 메뉴 이동이 명확합니다.

### 2) 상단 메뉴 라우팅 수정

- `home.html`: 상단 `My List` 탭을 `/my_list.html` 링크로 변경하고, 클릭 핸들러에서도 `list`는 로그인 무관 단순 이동으로 처리했습니다.
- `my.html`: 상단 `My List` 링크를 `/my_list.html`로 변경했습니다.

### 3) Home / My List 분리

- Home(`/home.html`)에서는 기존 기본 콘텐츠(캐릭터/세계관/게임 선택)만 보입니다.
- My List(`/my_list.html`)에서는 My List 전용 UI(탭/리스트/empty state)가 보입니다.

### 4) 로그인/비로그인 동작

- 비로그인 상태에서도 `/my_list.html` 진입 자체는 가능하며, 페이지 내부에서 `로그인이 필요합니다.` 토스트 + empty state로 안내합니다.

---

## Verification Steps (Ticket 기준)

1. `/home.html` 진입 후 상단 `My List` 메뉴 클릭
2. URL/화면이 `/my_list.html`로 전환되는지 확인
3. My List 진입 후 Home 기본 리스트가 아니라 My List 전용 UI가 보이는지 확인
4. **로그인 상태**에서 동일 동작 확인
5. **비로그인 상태**에서 동일 동작 확인 (진입은 되되, 내부 안내가 보이는지)
6. 다시 `Home`(Logo) 메뉴 클릭 시 `/home.html`로 정상 복귀하는지 확인

---

## Risks / Limitations

- 본 티켓은 네비게이션/진입점 수정이 목적이며, My Favorite 데이터 기능 신규 구현은 스코프 밖이라 `my_list.html`에서는 favorite 모드를 empty로 유지합니다.
- Release Verified는 Oracle VM 배포 환경에서 실제 브라우저로 확인이 필요합니다.

