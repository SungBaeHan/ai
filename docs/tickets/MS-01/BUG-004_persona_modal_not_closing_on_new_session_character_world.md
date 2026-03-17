# BUG-004 Persona Modal Not Closing on New Session (Character / World)

New session (no messages)에서 페르조나 선택 후 모달이 닫히지 않는 문제

---

# Metadata

Type: BUG  
Severity: major  
Layer: adapter  
Milestone: MS-01

---

# Problem

## Current behavior

- Character chat / World chat에서 **새 세션 (messages 0건)** 상태에서:
  - 페르조나 선택 모달이 정상적으로 뜸
  - 페르조나 선택 후 "완료" 클릭 시
  - **모달이 닫히지 않음**

- Game chat에서는:
  - 동일 상황에서 정상적으로 선택 후 모달 닫힘

---

## Expected behavior

- Character / World / Game 모든 채팅 타입에서:
  - 페르조나 선택 후 "완료" 클릭 시
  - 모달이 즉시 닫혀야 한다
  - 선택된 페르조나가 헤더 및 메시지에 반영되어야 한다

---

## Impact

- 새 유저 경험에서 UX break 발생
- 페르조나 선택 플로우가 완료되지 않는 느낌
- 실제로는 상태 반영되더라도 사용자 입장에서는 “동작하지 않는 것처럼” 보임

---

# Context

## Relevant files

- apps/web-html/chat.html
- apps/web-html/world.html
- apps/web-html/game.html

## Related functions (추정)

- confirmPersonaSelection()
- closePersonaModal()
- refreshHeaderPersonaBadge()
- getActivePersonaForSession()

## Key difference

- Game:
  - 세션이 없어도 정상적인 confirm → close flow 존재
- Character / World:
  - **session null 상태에서 confirm 이후 modal close가 실행되지 않음**

---

# Scope

## Allowed

- persona selection 관련 프론트 로직 수정
- modal close trigger 로직 수정
- session null 상태 처리 보강

## Not allowed

- API 변경
- DB 구조 변경
- persona 데이터 구조 변경
- 전반적인 UI 리팩토링

---

# Strategy

## Root cause hypothesis

1. confirmPersonaSelection() 내부에서:
   - session 존재 여부 기준 분기 존재
   - session이 없으면 closePersonaModal()이 호출되지 않음

2. async 처리 순서 문제:
   - persona 적용 → UI 업데이트 → modal close 순서가 깨짐

3. modal close가 특정 상태(CURRENT_SESSION 등)에 의존

---

## Recommended approach

- Game chat의 confirm flow를 기준으로 비교
- Character / World에서도 동일하게:

```js
confirmPersonaSelection() {
  // persona 적용 로직
  // ...

  closePersonaModal(); // 항상 실행되도록 보장
}