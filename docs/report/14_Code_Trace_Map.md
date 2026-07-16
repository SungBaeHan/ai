# 14. Code Trace Map

> 기능별 **Frontend → API → Service → DB** 추적표 (코드 기준, 2026-06-14)  
> 리팩토링·티켓 작성의 기준 문서

**범례:** `[x]` 연결 확인 · `[~]` 부분 · `[ ]` 없음 · `[?]` 확인 필요

---

## Character

| 화면/컴포넌트 | API Client | Router | Schema | Service | Repository/DB | Collection | 상태 |
|--------------|------------|--------|--------|---------|---------------|------------|------|
| `home.html` `loadCharactersPage` | `fetch` + `config.js` | `characters.py` `get_list` | 인라인 `CharacterIn` 등 | — | Mongo 직접 | `characters` | [x] |
| `search.html` | 동일 | `get_list` | 인라인 | — | Mongo 직접 | `characters` | [x] |
| `chat.html` `fetchCharacter` | `fetch` | `get_one` | 인라인 | — | Mongo 직접 | `characters` | [x] |
| `create/character.html` | `getAuthHeaders` + `fetch` | `create_character`, `ai-detail`, `upload-image` | 인라인 | — | Mongo + R2 | `characters` | [x] |
| `my_list.html` My Create | `Bearer` + `fetch` | `my_create.py` | — | — | Mongo 직접 | `characters` | [x] |
| `my_list.html` My Favorite | `fetch` | `characters.py` `get_my_characters` | — | — | Mongo 직접 | `characters` | [~] worlds/games 필터 프론트만 |
| `html/app/web` | — | — | — | — | — | — | [ ] 미배포 |

---

## NPC

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `create/game.html` 캐릭터 선택 | `fetch /v1/characters` | `games.py` `create_game` | `GameCharacterCreate` | `game_session.build_initial_characters_info` | Mongo | `characters`, `games` | [x] NPC=동일 엔티티 |
| `game.html` HUD NPC | session 응답 | `game_turn`, `games/session` | `GameSessionSnapshot` | `game_events` | Mongo | `game_session` | [x] |

---

## World

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `home.html` | `fetch` | `worlds.py` `list_worlds` | 인라인 `World` | — | Mongo 직접 | `worlds` | [x] |
| `world.html` | `fetch` + `Bearer` | `get_world`, `bootstrap`, `app_chat` | 인라인 | `chat_persist` | Mongo | `worlds`, `worlds_*` | [x] |
| `create/world.html` | `getAuthHeaders` | `create_world`, `ai-detail` | 인라인 | — | Mongo + R2 | `worlds` | [x] |

---

## Rule

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `create/game.html` rules 폼 | `meta` in FormData | `games.py` `create_game` | `GameRulesConfig` | — | Mongo | `games.rules` | [x] 저장 |
| 게임 턴 실행 | — | `game_turn.py` | — | `game_events` (events만) | Mongo | `games`, `game_session` | [~] 실행은 events 확률만 |
| LLM 프롬프트 | — | `game_turn.py` | — | — | — | — | [ ] rules 미전달 |

---

## Game

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `create/game.html` | `getAuthHeaders` | `games.py` POST | `GameCreateRequest` | `game_session` | Mongo | `games` | [x] |
| `game.html` | `Bearer` / `user_info_v2` | `get_game`, `session`, `turn`, `persona` | `game_turn.py` | `game_events`, `logging` | Mongo | `games`, `game_session` | [x] |
| `js/game_turn.js` | `callTurnApi` | `play_turn` | `GameTurnRequest/Response` | `game_events` | Mongo | `game_session` | [x] |
| `home.html` games 탭 | `fetch` | `list_games` | `GameListResponse` | — | Mongo | `games` | [x] |

---

## Chat

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `chat.html` | `Bearer` | `app_chat.py` POST `/v1/chat/` | 인라인 `ChatIn` | `chat_persist` | Mongo | `characters_*` | [x] |
| `world.html` | `Bearer` | `app_chat.py` | 인라인 | `chat_persist` | Mongo | `worlds_*` | [x] |
| — (프론트 미확인) | — | `chat_v2.py` | `schemas/chat_v2.py` | `OpenChatUseCase`, `SendMessageUseCase` | `MongoChatRepository` | `chat_*` | [?] API만 |
| `chat.html` bootstrap | `Bearer` | `characters.py` bootstrap | — | — | Mongo | `characters_session` | [x] |

---

## HUD / Status

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `game.html` `renderHudFromSession` | turn/session 응답 | `game_turn`, `games/session` | `GameSessionSnapshot` | delta 적용 in route | Mongo | `game_session` | [x] |
| `game.html` narration | `turn_logs` | `play_turn` | `TurnLog` | — | Mongo | `game_session` | [x] |
| 몬스터 HUD | — | — | — | — | — | — | [ ] 미구현 |

---

## Auth

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `my.html` | `fetch` Google/GIS | `auth_google.py` | `GoogleLoginRequest` | — | Mongo | `users` | [x] |
| 전 페이지 | `validate-session` | `auth.py` | `user_session.py` | — | Mongo | `users` | [x] |
| 보호 API | `Authorization: Bearer` | `deps/auth.py` | — | — | Mongo | `users` | [x] |
| create 페이지 | `getAuthHeaders` | 다수 | — | — | Mongo | `users` | [x] `user_info_v2` |

---

## My List

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `my_list.html` My Create | `Bearer` + headers | `my_create.py` | — | — | Mongo | `characters` | [x] |
| `my_list.html` My Favorite | `Bearer` | `characters/my`, `worlds`, `games` | — | — | Mongo | 다수 | [~] Favorite API 없음 |
| `my.html` | — | `auth/*` | — | — | — | — | [x] |
| `my_recent_characters.html` | — | — | — | — | — | — | [ ] placeholder |

---

## Admin

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| — | — | — | — | — | — | — | [ ] 미구현 |
| — | — | `debug_db.py`, `migrate.py` | — | — | — | — | [x] ops only, 무인증 |

---

## Image / Upload

| 화면 | API Client | Router | Schema | Service | DB | Collection | 상태 |
|------|------------|--------|--------|---------|-----|------------|------|
| `create/*.html` | FormData | `upload-image` routes | — | R2 adapter | Mongo optional | `images` | [x] |
| `personas.html` | `X-User-Info-Token` | `uploads/persona-image` | 인라인 | R2 | — | — | [x] |
| `home.html` gallery | `fetch` | `assets.py` | `ImageListResponse` | — | Mongo | `images` | [x] |
| CDN | `config.js` `ASSET_BASE_URL` | — | — | — | — | — | [x] |

---

## LLM

| 흐름 | API Client | Router | Prompt | Service | Parser | 상태 |
|------|------------|--------|--------|---------|--------|------|
| 게임 턴 | `game.html` | `game_turn.py` | `trpg_game_master.py` | `game_events` | `GameTurnLLMResponse` | [x] |
| TRPG 채팅 | `chat/world.html` | `app_chat.py` | `SYS_TRPG*` inline | `chat_persist` | `postprocess_trpg` | [x] |
| AI detail | `create/*.html` | `ai-detail` routes | inline prompt | — | JSON | [x] |
| Chat V2 | [?] | `chat_v2.py` | [?] | usecase | [?] | [?] |
| RAG ask | — | `ask.py` | — | Qdrant | — | [~] compose만 |

---

## 공통 Frontend 인프라

| 파일 | 역할 |
|------|------|
| `apps/web-html/js/config.js` | `API_BASE`, `apiFetch`, `logEvent`, `X-Anon-Id` |
| `apps/web-html/static/js/session.js` | `getAuthHeaders`, `checkAccountStatus` |
| `apps/web-html/static/js/infinite-scroll.js` | 목록 페이징 |

> **확인 필요:** `personas.html`이 `/js/session.js` 참조하나 파일은 `static/js/session.js`에 존재.

---

## 아키텍처 목표 vs 현실

| 패턴 | 적용 사례 | 미적용 사례 |
|------|----------|------------|
| Route→Usecase→Adapter | `chat_v2.py` | `characters`, `worlds`, `games`, `game_turn` |
| Route→Service→Mongo | `app_chat`, `game_turn` | — |
| Route→Mongo 직접 | 대부분 CRUD | — |

**SSOT 정책:** 신규 코드는 Route→Usecase→Adapter (`docs/SSOT.md`)  
**코드 현실:** 레거시 direct Mongo 다수 (`docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`)

---

## 분석 기준 파일

- `apps/web-html/**/*.html`, `js/config.js`, `static/js/session.js`
- `apps/api/routes/*.py`, `apps/api/services/*.py`
- `src/usecases/`, `adapters/persistence/mongo/`
- `apps/api/schemas/`, `apps/api/models/games.py`
