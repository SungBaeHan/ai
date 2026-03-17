# BUG-003 Persona Not Rendered in New Chat Sessions — 분석

**티켓:** [BUG-003 Persona Not Rendered in New Chat Sessions](../tickets/MS-01/BUG-003_persona_not_rendered_in_new_chat_sessions.md)  
**분석일:** 2025-03-13  
**상태:** 분석 완료 (구현 완료 후 검증 완료)  
**최종 검증 보고서:** [BUG-003-verification-report.md](./BUG-003-verification-report.md)

---

## 1. Root Cause (근본 원인)

### 1.1 요약

**새 채팅 세션(메시지 0건)에서 API가 `session: null`을 주고, 프론트엔드는 “세션이 있을 때만” 페르조나 목록 로드 및 헤더 배지 갱신을 하기 때문에, 새 세션 진입 시 페르조나 선택기와 메시지 옆 페르조나 배지가 나오지 않는다.**

- **Character chat:** 새 세션(메시지 없음)일 때 `PERSONAS_LIST`를 아예 로드하지 않고, `refreshHeaderPersonaBadge()`는 `CURRENT_SESSION`이 있을 때만 호출됨.
- **World chat:** 새 세션일 때 `session`이 있을 때만 `PERSONAS_LIST` 로드 + `refreshHeaderPersonaBadge()` 호출. `session === null`이면 둘 다 생략.
- **Game chat:** 세션 없을 때도 `PERSONAS_LIST` 로드 후 `refreshHeaderPersonaBadge()` 호출하므로 동작은 맞고, “동작 불일치”는 세션 갱신 후 헤더를 의도적으로 갱신하지 않는 부분과 혼재된 것으로 보임.

### 1.2 API 동작

- **Character bootstrap** (`GET /v1/characters/{id}/chat/bootstrap`):  
  (user_id, character_id)로 세션 조회. **세션이 없으면** `{ session: null, messages: [] }` 반환. 세션 있으면 `session`에 `persona` 포함 가능.
- **World bootstrap** (`GET /v1/worlds/{id}/chat/bootstrap`):  
  (user_id, world_id)로 세션 조회. **세션이 없으면** `{ session: null, messages: [] }` 반환.
- 즉, “처음 들어온 새 채팅”은 **세션이 아직 없음** → `session === null`이 정상.

### 1.3 프론트엔드 동작 (문제 지점)

| 화면 | `messages.length === 0` (새 세션) 시 동작 | 문제 |
|------|-------------------------------------------|------|
| **Character (chat.html)** | `PERSONAS_LIST`는 **메시지가 있을 때만** 로드. `refreshHeaderPersonaBadge()`는 **`CURRENT_SESSION`이 있을 때만** 호출. | 새 세션에선 `PERSONAS_LIST` 미로드 + 헤더 갱신 미호출 → 선택기/배지 없음. 첫 메시지 시 `getActivePersonaForSession()`도 목록이 비어 있어 페르조나 배지 미표시. |
| **World (world.html)** | `session`이 있을 때만 `PERSONAS_LIST` 로드 + `refreshHeaderPersonaBadge()` 호출. | 새 세션(`session === null`)에선 둘 다 생략 → 선택기/배지 없음. |
| **Game (game.html)** | `sessionData` 없어도 `PERSONAS_LIST` 로드 후 `refreshHeaderPersonaBadge()` 호출. | 새 세션에서도 헤더는 처리됨. (다만 턴 후 세션 갱신 시 헤더를 안 갱신하는 로직이 있어 “동작 불일치”처럼 보일 수 있음) |

정리하면:

- **근본 원인:** 새 채팅 = `session === null`인데, Character/World는 “세션이 있을 때만” 페르조나 초기화(목록 로드 + 헤더 배지 갱신)를 하도록 되어 있음.
- **2차 원인 (Character):** 메시지가 0건인 분기에서는 `PERSONAS_LIST`를 아예 fetch하지 않아, 나중에 첫 메시지를 보내도 `getActivePersonaForSession()`이 기본 페르조나를 못 찾고, 메시지 옆 페르조나 배지도 안 나옴.

---

## 2. 관련 파일

### 2.1 수정 대상 (우선)

| 파일 | 역할 | 수정 포인트 |
|------|------|-------------|
| `apps/web-html/chat.html` | 캐릭터 채팅 | 새 세션(메시지 0건) 분기에서도 `PERSONAS_LIST` 로드 + 무조건 `refreshHeaderPersonaBadge()` 호출. |
| `apps/web-html/world.html` | 세계관 채팅 | 새 세션(메시지 0건) 분기에서도 `session` 여부와 관계없이 `PERSONAS_LIST` 로드 + `refreshHeaderPersonaBadge()` 호출. |

### 2.2 참고 (동작 확인/정렬용)

| 파일 | 역할 |
|------|------|
| `apps/web-html/game.html` | 게임 채팅. 세션 없을 때도 페르조나 로드·헤더 갱신 함. Character/World와 동작 정렬 시 참고. |
| `apps/api/routes/characters.py` | `bootstrap_character_chat`: 세션 없으면 `session: null` 반환. |
| `apps/api/routes/worlds.py` | `bootstrap_world_chat`: 세션 없으면 `session: null` 반환. |

API는 “세션 없음”을 null로 주는 것이 맞고, 티켓 스코프상 DB/인프라 변경 없이 **프론트엔드에서 새 세션일 때도 페르조나를 보여 주는 쪽으로 수정**하는 것이 적절함.

---

## 3. 왜 새 채팅 세션에서 페르조나가 안 나오는가

1. 사용자가 **처음** 캐릭터/세계관 채팅에 들어감 → bootstrap 호출.
2. 아직 대화 기록이 없어 세션이 생성되지 않음 → API가 `{ session: null, messages: [] }` 반환.
3. **Character:**  
   - `messages.length === 0`이므로 “메시지 있음” 분기로 가지 않음.  
   - 이 분기에서는 `PERSONAS_LIST`를 fetch하지 않음.  
   - `refreshHeaderPersonaBadge()`는 `if (CURRENT_SESSION)` 안에서만 호출되는데, `CURRENT_SESSION === null`이라 호출되지 않음.  
   → 헤더 페르조나 선택기/배지 없음. 나중에 첫 메시지를 보내도 `PERSONAS_LIST`가 비어 있어 `getActivePersonaForSession()`이 null → 메시지 옆 페르조나도 안 나옴.
4. **World:**  
   - `messages.length === 0`이고 `session === null`이므로 `if (session)` 안의 `PERSONAS_LIST` 로드와 `refreshHeaderPersonaBadge()`가 실행되지 않음.  
   → 헤더에 페르조나 선택기/배지 없음. (세션이 있으면 이 블록이 실행되어 표시됨.)

즉, “새 세션 = session null”인 경우를 전제로 한 초기화가 빠져 있어서, 페르조나가 안 나오는 것이다.

---

## 4. Working vs Broken Flow 비교

### 4.1 정상 동작 (기존 채팅 세션 — 메시지 있음)

- Bootstrap → `session` 있음, `messages.length > 0`.
- **Character:**  
  `PERSONAS_LIST` fetch → 메시지 렌더 → `refreshAllUserMessageBadges()` → `refreshHeaderPersonaBadge()`.
- **World:**  
  `CURRENT_WORLD_SESSION = session` → 메시지 렌더 → `PERSONAS_LIST` fetch → `refreshAllUserMessageBadges()` → `refreshHeaderPersonaBadge()`.
- 결과: 헤더에 페르조나 선택기/배지 표시, 유저 메시지 옆에도 페르조나 배지 표시.

### 4.2 깨진 동작 (새 채팅 세션 — 메시지 0건)

- Bootstrap → `session === null`, `messages.length === 0`.
- **Character:**  
  - `PERSONAS_LIST` fetch 없음.  
  - `if (CURRENT_SESSION) { refreshHeaderPersonaBadge(); }` → false라 호출 안 함.  
  - 결과: 헤더에 페르조나 없음. 첫 메시지 시에도 `PERSONAS_LIST`가 비어 있어 메시지 옆 페르조나 없음.
- **World:**  
  - `if (session)` 블록 전체 스킵 → `PERSONAS_LIST` 로드 없음, `refreshHeaderPersonaBadge()` 호출 없음.  
  - 결과: 헤더에 페르조나 없음.
- **Game:**  
  - `sessionData` 없어도 `PERSONAS_LIST` 로드 후 `refreshHeaderPersonaBadge()` 호출하므로, 새 세션에서도 헤더에는 페르조나가 나옴 (정상).

---

## 5. 구현 계획 (Implementation Plan)

### 5.1 원칙

- 새 세션(`session === null` 또는 `messages.length === 0`)에서도 **항상**  
  - 페르조나 목록(`PERSONAS_LIST`)을 로드하고  
  - 헤더 배지/선택기(`refreshHeaderPersonaBadge()`)를 한 번 갱신한다.  
- `getActivePersonaForSession()`은 이미 “세션 persona 없으면 PERSONAS_LIST 기본값”으로 동작하므로, 목록만 채워주면 헤더/메시지 배지 모두 기본 페르조나로 표시 가능.

### 5.2 chat.html (Character) 수정

- **위치:** `DOMContentLoaded` 내부, bootstrap 후 `messages.length === 0`인 `else` 분기.
- **현재:**  
  - `PERSONAS_LIST`는 이 분기에서 로드하지 않음.  
  - `if (CURRENT_SESSION) { refreshHeaderPersonaBadge(); }` 만 있음.
- **변경:**  
  1. 메시지가 0건이어도 **무조건** `PERSONAS_LIST = await fetchPersonas()` (기존 fetchPersonas 사용, try/catch 유지).  
  2. `if (CURRENT_SESSION)` 제거하고 **항상** `refreshHeaderPersonaBadge()` 호출.  
- **결과:** 새 세션에서도 헤더에 페르조나 선택기/배지 표시, 첫 메시지 시 `getActivePersonaForSession()`이 `PERSONAS_LIST` 기본값을 써서 메시지 옆 배지도 표시.

### 5.3 world.html (World) 수정

- **위치:** `DOMContentLoaded` 내부, bootstrap 후 `messages.length === 0`인 `else` 분기.
- **현재:**  
  - `if (session) { PERSONAS_LIST fetch; refreshHeaderPersonaBadge(); }` 만 있음.
- **변경:**  
  1. `if (session)` 제거.  
  2. 메시지가 0건인 분기에서 **항상** `PERSONAS_LIST` fetch (동일하게 try/catch 유지).  
  3. **항상** `refreshHeaderPersonaBadge()` 호출.  
- **결과:** 새 세션(`session === null`)에서도 헤더에 페르조나 선택기/배지 표시, 첫 메시지 시 메시지 옆 페르조나 배지도 기본 페르조나로 표시.

### 5.4 game.html

- 현재도 세션 없을 때 `PERSONAS_LIST` 로드 + `refreshHeaderPersonaBadge()` 호출하고 있으므로 **이번 버그 수정 범위에서는 변경 없음**.  
- 필요하면 “세션 갱신 후에도 헤더 페르조나 갱신 여부”는 별도 티켓으로 정리하는 것을 권장.

### 5.5 검증

- Character: 홈에서 캐릭터 채팅 진입 → 새 채팅에서 상단 페르조나 선택기 표시, 메시지 전송 시 오른쪽 페르조나 배지 표시.
- World: 동일하게 새 세계관 채팅 진입 → 상단 페르조나 선택기 및 메시지 옆 배지 표시.
- Game: 새 게임 채팅 진입 시 기존처럼 페르조나 표시 유지.
- 기존 채팅(이미 메시지 있는 세션) 재진입 시 기존처럼 동작하는지 회귀 테스트.

---

## 6. 요약

| 항목 | 내용 |
|------|------|
| **Root cause** | 새 채팅 세션에서 API가 `session: null`을 주는데, Character/World는 “세션이 있을 때만” 페르조나 목록 로드 및 헤더 배지 갱신을 해서, 새 세션에서 선택기/배지가 안 나옴. Character는 0건 분기에서 `PERSONAS_LIST` 자체를 로드하지 않아 첫 메시지 옆 배지도 안 나옴. |
| **수정 파일** | `apps/web-html/chat.html`, `apps/web-html/world.html` |
| **구현 방향** | 새 세션(메시지 0건) 분기에서도 **항상** `PERSONAS_LIST` 로드 + `refreshHeaderPersonaBadge()` 호출. (Character: 0건 분기에 목록 로드 추가 + 조건 없이 헤더 갱신, World: `if (session)` 제거 후 동일하게 항상 로드·갱신) |

이 계획대로 적용하면 BUG-003에서 기대하는 “모든 채팅 화면에서 새 세션 진입 시에도 페르조나 선택기 및 메시지 옆 페르조나 표시”를 만족할 수 있다.

---

## 7. 검증 완료 (사후)

- 구현 반영 후 Acceptance Criteria 7항목 및 새 세션/기존 세션/persona 변경/API 실패 시나리오에 대해 코드 기준 검증 완료.
- Game chat은 수정 없이 동일 기준 충족 확인.
- **최종 보고서:** [BUG-003-verification-report.md](./BUG-003-verification-report.md)
