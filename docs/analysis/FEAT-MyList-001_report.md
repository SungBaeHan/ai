# FEAT-MyList-001 My List 메뉴 구조 구성 — Implementation Report

**Ticket:** `docs/tickets/MS-03/FEAT-MyList-001-my-list-navigation-structure.md`  
**Report location:** `docs/analysis/FEAT-MyList-001_report.md`  
**Date:** 2025-02-27

---

## Completion Status

- Implementation Done: **YES**
- Release Verified: **PENDING**

---

## Summary

`My List` 화면(현재 `apps/web-html/home.html`)에 아래 UI 구조를 추가했습니다.

- **1Depth:** `My Create` / `My Favorite`
- **2Depth:** 기존 `캐릭터 / 세계관 / 게임` 선택 UI를 그대로 유지하며, 1Depth 모드에 따라 데이터 로딩/필터만 변경

**중요:** 기존 카드 UI(캐릭터/세계관/게임 카드 생성 함수)는 수정하지 않고 그대로 재사용했습니다.

---

## Files Changed

- `apps/web-html/home.html`

---

## Key Changes

### 1) UI 구조 (탭)

- `My Create` / `My Favorite` 1Depth 탭을 추가했습니다.
- 기존 `캐릭터/세계관/게임` 탭은 2Depth로 유지했습니다.

### 2) Data source rules 반영

- **My Create**
  - **캐릭터:** `GET /v1/characters/my` 사용 (creator 기준)
  - **세계관:** `GET /v1/worlds`로 가져온 뒤, `reg_user`가 현재 사용자(`google_id` 또는 `email`)와 일치하는 항목만 프론트에서 필터
  - **게임:** `GET /v1/games`로 가져온 뒤, `reg_user`가 현재 사용자(`google_id` 또는 `email`)와 일치하는 항목만 프론트에서 필터
- **My Favorite**
  - 현재 백엔드에 favorites 관련 API/데이터 접근 경로가 repo 내에 존재하지 않아(검색 결과 없음), UI 구조는 제공하되 리스트는 빈 결과로 표시됩니다.

---

## Verification Steps (Ticket 기준)

1. `My List` 진입 (`/home.html`)
2. **My Create** 클릭 → **캐릭터 선택** → 리스트가 출력되는지 확인  
   - 로그인 상태에서 `/v1/characters/my` 호출 성공 확인
3. **My Favorite** 클릭 → **세계관 선택** → 리스트 UI가 정상 동작(빈 리스트 포함)하는지 확인
4. 각 카드 클릭 시 정상 이동 확인  
   - 캐릭터: `/chat?character=...`  
   - 세계관: `/world.html?world=...`  
   - 게임: `/game.html?game=...`

---

## Notes / Risks

1. **My Favorite 데이터 소스 미구현**  
   - 티켓 요구사항의 “favorites collection(user_id 기준)”을 충족하려면, 백엔드에 favorites 조회 API(또는 기존 API 확장)가 필요합니다.  
   - 본 티켓 스코프에서 “API 구조 변경”은 금지되어 있어 프론트 단에서 UI 구조만 우선 반영했습니다.

2. **World/Game My Create의 owner_id 해석**  
   - 현재 World/Game 문서에는 `owner_id` 필드가 아니라 `reg_user(google_id/email)`가 저장됩니다.  
   - 따라서 “현재 사용자 기준” 필터를 `reg_user` 매칭으로 구현했습니다(스키마/API 변경 없이 충족 가능한 최소 방식).

