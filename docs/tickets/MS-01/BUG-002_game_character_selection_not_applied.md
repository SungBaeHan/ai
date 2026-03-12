# BUG-002 — Game Creation Character Selection Not Applied

## Metadata

Severity: major  
Layer: game / api  
Milestone: MS-01_Stabilization

---

## Description

게임 생성 화면에서 캐릭터를 선택한 후 게임을 생성해도  
선택한 캐릭터 정보가 게임 메타에 반영되지 않는 문제가 발생한다.

UI 상에서는 캐릭터가 선택된 것처럼 보이지만  
게임 생성 이후 생성된 게임 데이터에는 캐릭터 정보가 존재하지 않는다.

이 문제로 인해

- 캐릭터 기반 게임 생성이 정상적으로 동작하지 않음
- 플레이 시작 시 캐릭터 정보가 누락됨
- 캐릭터 스탯 및 속성 기반 게임 로직이 정상 작동하지 않을 가능성이 있음

---

## Reproduction Steps

1. 게임 생성 화면 진입
2. 캐릭터 선택
3. 게임 메타 설정 입력
4. 게임 생성 버튼 클릭

---

## Expected Result

선택한 캐릭터 정보가

- 게임 생성 API payload에 포함되고
- 서버에서 게임 메타에 저장된다

생성된 게임에서 캐릭터가 정상적으로 표시되고  
게임 플레이 시 해당 캐릭터가 적용된다.

---

## Actual Result

- 게임 생성은 정상적으로 수행됨
- 캐릭터 정보가 API 요청에 포함되지 않거나
- 서버에서 저장되지 않음
- 생성된 게임에서 캐릭터가 없는 상태로 시작됨

---

## Environment

env: dev  
browser: Chrome  
device: Desktop

---

## Technical Context

현재 게임 생성 흐름은 다음과 같다.


game_create.html
↓
game_create.js
↓
POST /api/game/create
↓
routers/game.py
↓
services/game_service.py
↓
game meta 저장


문제 가능 영역

- 프론트엔드에서 character_id를 payload에 포함하지 않음
- API 요청 시 form state 값 누락
- 서버에서 character_id 처리 로직 미구현
- game meta 저장 시 character 필드 누락

---

## Implementation Strategy

Possible fixes:

1. Ensure `character_id` is included in the game creation request payload.
2. Verify `routers/game.py` receives and forwards the value correctly.
3. Confirm `game_service.py` persists the character reference in the game meta.
4. Ensure existing game creation flow remains unchanged.

Do NOT modify:

- database schema
- session snapshot logic
- message/event system
- existing API contracts unless necessary

---

## Acceptance Criteria

다음 조건을 만족하면 완료로 간주한다.

- 캐릭터 선택 후 게임 생성 시 `character_id`가 API payload에 포함된다
- 서버에서 해당 값이 게임 메타에 저장된다
- 생성된 게임에서 캐릭터가 정상적으로 표시된다
- 기존 게임 생성 기능에 영향이 없다

---

## Verification

1. API 서버 실행
2. 게임 생성 화면 진입
3. 캐릭터 선택
4. 게임 생성 실행
5. Network 요청 확인
6. payload에 `character_id` 존재 확인
7. 생성된 게임 메타에서 character reference 확인

---

## Output Format

Before coding provide:

- root cause
- files to change
- implementation plan

After coding provide:

- files changed
- summary of fix
- verification steps
- potential risks

---

## Related Tickets

BUG-001_character_cdn.md