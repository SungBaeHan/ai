# BUG-004 Persona Modal Not Closing on New Session — 처리 결과 보고서

**티켓:** [BUG-004 Persona Modal Not Closing on New Session (Character / World)](../tickets/MS-01/BUG-004_persona_modal_not_closing_on_new_session_character_world.md)  
**처리일:** 2025-02-27  
**상태:** 구현 완료

---

## 1. 문제 요약

- **Character chat / World chat**에서 **새 세션(메시지 0건)**일 때:
  - 페르조나 선택 모달은 정상 표시
  - 페르조나 선택 후 "완료" 클릭 시 **모달이 닫히지 않음**
- **Game chat**에서는 동일 상황에서 모달이 정상적으로 닫힘

---

## 2. 원인 분석 (Root Cause)

- `confirmPersonaSelection()` 내부에서 **세션 존재 여부**를 먼저 검사함.
  - Character: `if (!CURRENT_SESSION || !CURRENT_SESSION.id) { showToast('...'); return; }`
  - World: `if (!CURRENT_WORLD_SESSION || !CURRENT_WORLD_SESSION.id) { showToast('...'); return; }`
- 새 세션에서는 bootstrap이 `session: null`을 반환하므로 `CURRENT_SESSION` / `CURRENT_WORLD_SESSION`이 **null**.
- 위 조건에서 **early return**만 하고 `closePersonaModal()`을 호출하지 않아, 모달이 닫히지 않음.
- Game은 세션 없을 때도 confirm 후 close를 수행하는 흐름이 있어 별도 수정 없음.

---

## 3. 수정 파일 및 변경 내용

| 파일 | 변경 내용 |
|------|------------|
| **apps/web-html/chat.html** | ① 전역 `PENDING_PERSONA_ID` 추가 ② 세션 없을 때 early return 대신 `PENDING_PERSONA_ID` 설정 → `refreshHeaderPersonaBadge()` → `closePersonaModal()` → 토스트 후 return ③ `getActivePersonaForSession()`에서 세션 persona 없을 때 `PENDING_PERSONA_ID`로 PERSONAS_LIST 조회해 반환 ④ API 적용 성공 시 `PENDING_PERSONA_ID = null` 처리 |
| **apps/web-html/world.html** | 동일 패턴 적용 (CURRENT_WORLD_SESSION, PENDING_PERSONA_ID) |
| **apps/web-html/game.html** | 변경 없음 (티켓 범위 외) |

---

## 4. 구현 상세

### 4.1 새 세션(session null)에서 "완료" 클릭 시

- **기존:** 세션 없음 → 토스트만 띄우고 `return` → `closePersonaModal()` 미호출 → 모달 유지.
- **변경:** 세션 없음 → `PENDING_PERSONA_ID = SELECTED_PERSONA_ID` → `refreshHeaderPersonaBadge()` → **`closePersonaModal()`** → 토스트("페르조나가 선택되었습니다. 메시지를 보내면 적용됩니다.") → `return`.
- 그 결과 모달은 항상 닫히고, 헤더에는 선택한 페르조나가 표시됨.

### 4.2 PENDING_PERSONA_ID

- 새 세션에서는 API로 세션에 persona를 저장할 수 없으므로, 선택만 **로컬 상태**로 보관.
- `getActivePersonaForSession()`에서:
  1. 세션 persona 있음 → 세션 값 사용
  2. 없고 `PENDING_PERSONA_ID` 있음 → PERSONAS_LIST에서 조회해 반환 (헤더·메시지 배지용)
  3. 그 외 → PERSONAS_LIST 기본값
- 첫 메시지 전송 시에도 선택한 페르조나가 유저 메시지 옆에 표시됨.

### 4.3 API 적용 성공 시

- 세션에 persona 적용이 성공하면 `PENDING_PERSONA_ID = null`로 초기화하여, 이후에는 세션 persona만 사용하도록 함.

---

## 5. 검증 방법

1. **Character 새 세션:** 홈 → 캐릭터 선택 → 한 번도 대화하지 않은 캐릭터 채팅 진입 → Persona 모달 열기 → 페르조나 선택 → "완료" 클릭 → **모달이 즉시 닫히는지**, 헤더에 선택한 페르조나가 표시되는지 확인.
2. **World 새 세션:** 동일하게 한 번도 대화하지 않은 세계관 채팅에서 같은 절차로 모달 닫힘 및 헤더 반영 확인.
3. 위 상태에서 메시지 1건 전송 → 유저 메시지 옆에 선택한 페르조나 아이콘 표시 확인.
4. **기존 세션:** 이미 메시지가 있는 캐릭터/세계관 채팅에서 Persona 변경 후 "완료" → 모달 닫힘 및 적용 유지(회귀 없음) 확인.

---

## 6. 위험·참고 사항

- 새 세션에서 선택한 페르조나는 **로컬(PENDING_PERSONA_ID)**만 반영됨. 첫 메시지로 세션이 생성된 뒤, 필요 시 다시 Persona 모달에서 "완료"하면 그때 API로 세션에 저장됨.
- API·DB·인프라·game.html은 변경하지 않았음.

---

## 7. 결론

- 새 세션(Character/World)에서 페르조나 "완료" 클릭 시 **모달이 항상 닫히도록** 수정함.
- 선택한 페르조나는 헤더 및 유저 메시지 영역에 반영되며, 기존 세션 동작은 유지됨.
- BUG-004 티켓 범위 내 처리 완료.
