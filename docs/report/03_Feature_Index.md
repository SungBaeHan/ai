# 03. Feature Index

> `apps/web-html/`, `apps/api/routes/` 코드 기준 (2026-06-14)  
> 범례: `[x]` 구현 · `[~]` 부분 구현 · `[ ]` 미구현 · `[?]` 확인 필요

---

## Character

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 캐릭터 목록 | [x] | `home.html` | `GET /v1/characters` | `routes/characters.py` | `characters` | |
| 캐릭터 상세 | [x] | `character.html` | `GET /v1/characters/{id}` | `routes/characters.py` | `characters` | |
| 캐릭터 생성 | [x] | `create/character.html` | `POST /v1/characters` | `routes/characters.py` | `characters` | 이미지+R2 |
| AI 상세 생성 | [x] | `create/character.html` | `POST /v1/characters/ai-detail` | `routes/characters.py` | — | OpenAI |
| 이미지 업로드 | [x] | `create/character.html` | `POST /v1/characters/upload-image` | `routes/characters.py` | R2 | |
| 내 캐릭터 목록 | [x] | `my_create_characters.html` | `GET /v1/characters/my` | `routes/characters.py` | `characters` | |
| 캐릭터 채팅 (TRPG) | [x] | `chat.html` | `POST /v1/chat/` | `routes/app_chat.py` | `character_sessions` | V1 |
| 채팅 bootstrap | [x] | `chat.html` | `GET /v1/characters/{id}/chat/bootstrap` | `routes/characters.py` | `character_sessions` | |
| Chat V2 | [?] | — | `POST /chat/v2/...` | `routes/chat_v2.py` | `chats_v2` | 프론트 연결 미확인 |

---

## NPC

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| NPC 전용 CRUD | [ ] | — | — | — | — | `characters` 재사용 |
| 게임 동료 NPC | [x] | `create/game.html` | `POST /v1/games` | `routes/games.py` | `games.characters[]` | |
| 세션 NPC 정보 | [x] | `game.html` | `GET /v1/games/{id}/session` | `routes/games.py`, `game_session.py` | `game_sessions.characters_info` | |

---

## World / Worldview

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 세계관 목록/상세 | [x] | `world.html` | `GET /v1/worlds`, `GET /v1/worlds/{id}` | `routes/worlds.py` | `worlds` | |
| 세계관 생성 | [x] | `create/world.html` | `POST /v1/worlds` | `routes/worlds.py` | `worlds` | |
| AI 세계관 상세 | [x] | `create/world.html` | `POST /v1/worlds/ai-detail` | `routes/worlds.py` | — | OpenAI |
| 세계관 채팅 | [x] | `world.html` | `POST /v1/chat/` | `routes/app_chat.py` | `world_sessions` | |
| 채팅 bootstrap | [x] | `world.html` | `GET /v1/worlds/{id}/chat/bootstrap` | `routes/worlds.py` | `world_sessions` | |

---

## Rule / Rulebook

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 룰 설정 UI | [x] | `create/game.html` | — | — | — | dice/damage/critical |
| rules 저장 | [x] | `create/game.html` | `POST /v1/games` | `routes/games.py` | `games.rules` | |
| rules LLM 전달 | [ ] | — | `POST /v1/games/{id}/turn` | `routes/game_turn.py` | — | 저장만, 미전달 |
| events 확률 전투 | [~] | `game.html` | `POST /v1/games/{id}/turn` | `services/game_events.py` | `games.rules.events` | events만 |
| 주사위/데미지 실행 | [ ] | — | — | — | — | 공식 실행 로직 없음 |

---

## Game

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 게임 생성 | [x] | `create/game.html` | `POST /v1/games` | `routes/games.py` | `games`, `game_sessions` | |
| 게임 목록/상세 | [x] | `my_list.html` 등 | `GET /v1/games` | `routes/games.py` | `games` | |
| 세션 조회 | [x] | `game.html` | `GET /v1/games/{id}/session` | `routes/games.py` | `game_sessions` | |
| 턴 진행 (LLM JSON) | [x] | `game.html` | `POST /v1/games/{id}/turn` | `routes/game_turn.py` | `game_sessions` | |
| 랜덤 전투 이벤트 | [x] | `game.html` | `POST /v1/games/{id}/turn` | `services/game_events.py` | `game_sessions` | |
| 페르소나 설정 | [x] | `game.html` | `POST /v1/games/{id}/persona` | `routes/games.py` | `games` | |
| phase FSM | [ ] | — | — | — | `game_sessions.phase` | 저장만 |
| 게임 종료 UI | [ ] | — | — | — | — | 세션은 지속 저장 |

---

## Chat

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| TRPG 채팅 V1 | [x] | `chat.html`, `world.html` | `POST /v1/chat/` | `routes/app_chat.py` | `character_sessions`, `world_sessions` | |
| QA 모드 | [x] | `chat.html` | `POST /v1/chat/` | `routes/app_chat.py` | — | mode=qa |
| 선택지 후처리 | [x] | `chat.html` | — | `app_chat.py` `postprocess_trpg` | — | |
| Chat V2 API | [x] | — | `/chat/v2/...` | `routes/chat_v2.py`, `usecases/chat_v2.py` | `chats_v2` | FE 미확인 |
| RAG (Qdrant) | [ ] | — | — | `app_chat.py` | Qdrant | `context=""` OFF |
| 단순 질의 | [x] | — | `POST /v1/ask` | `routes/ask.py` | — | |

---

## HUD / Status

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| HP/MP/Gold HUD | [x] | `game.html` | `GET /session`, `POST /turn` | `routes/game_turn.py` | `game_sessions.player` | `renderHudFromSession` |
| 전투 상태 표시 | [~] | `game.html` | `POST /turn` | `routes/game_turn.py` | `game_sessions.combat` | LLM 신뢰 |
| 인벤토리 HUD | [?] | `game.html` | — | — | `game_sessions.inventory` | UI 범위 확인 필요 |

---

## Auth

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| Google OAuth | [x] | `my.html` | `POST /v1/auth/google` | `routes/auth_google.py` | `users` | |
| JWT access_token | [x] | `my.html` | — | `auth_google.py` | — | |
| user_info_v2 | [x] | `my.html` | `POST /v1/auth/validate-session` | `deps/auth.py` | `users` | |
| 로그아웃 | [x] | `my.html` | — | — | — | localStorage |
| 계정 잠금/비활성 | [x] | — | `validate-session` | `deps/auth.py` | `users` | is_lock, is_use |

---

## My List

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| My 메뉴 | [x] | `my.html` | — | — | — | |
| My List | [x] | `my_list.html` | `GET /v1/games` 등 | `routes/games.py` | `games` | |
| 최근 플레이 캐릭터 | [~] | `my_recent_characters.html` | — | — | — | placeholder UI |
| 내 생성 목록 | [x] | `my_create_*.html` | `/api/my-create/*` | `routes/my_create.py` | 다수 | |

---

## Admin / Back Office

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| Admin UI | [ ] | — | — | — | — | |
| Debug DB | [x] | — | `GET /_debug/db` | `main.py` | — | 운영 차단 필요 |
| Mongo ping | [x] | — | `GET /v1/debug/mongo-ping` | `main.py` | — | |
| SQLite→Mongo 마이그레이션 | [x] | — | `POST /_ops/migrate/...` | `main.py` | — | ops |

---

## Upload / Image

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 캐릭터 이미지 | [x] | `create/character.html` | `POST /v1/characters/upload-image` | `routes/characters.py` | R2 | |
| 페르소나 이미지 | [x] | `personas.html` | `POST /v1/uploads/persona-image` | `routes/uploads.py` | R2 | |
| CDN URL | [x] | 전역 | — | `r2_storage.py` | — | `img.arcanaverse.ai` |
| 이미지 목록 | [x] | — | `GET /assets/images` | `routes/assets.py` | R2 | |

---

## LLM / AI

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 게임 턴 GM (JSON) | [x] | `game.html` | `POST /v1/games/{id}/turn` | `game_turn.py`, `trpg_game_master.py` | — | gpt-4o-mini |
| TRPG 채팅 | [x] | `chat.html` | `POST /v1/chat/` | `app_chat.py` | — | |
| 캐릭터 AI 생성 | [x] | `create/character.html` | `POST .../ai-detail` | `characters.py` | — | |
| 세계관 AI 생성 | [x] | `create/world.html` | `POST .../ai-detail` | `worlds.py` | — | |
| Ollama Provider | [~] | — | — | `llm_client.py` | — | compose 비활성 |
| 토큰/비용 관리 | [ ] | — | — | — | — | 미구현 |

---

## Deployment

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| Docker Compose | [x] | — | — | `infra/docker-compose.yml` | — | |
| Nginx 리버스 프록시 | [x] | — | — | `infra/nginx/` | — | |
| Cloudflare Pages (FE) | [x] | — | — | `apps/web-html/` | — | arcanaverse.ai |
| Oracle VM 배포 | [?] | — | — | `infra/README-OPERATIONS.md` | — | 문서 기준 |
| 로깅 API | [x] | — | `POST /v1/logs/*` | `routes/logs.py` | `access_logs` 등 | |

---

## Persona (보조 도메인)

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| 페르소나 CRUD | [x] | `personas.html` | `/v1/users/me/personas` | `routes/personas.py` | `personas` | |
| 프리셋 16종 | [x] | `personas.html` | `GET /v1/personas/presets` | `routes/personas.py` | — | |
| 게임/채팅 적용 | [x] | `game.html`, `chat.html` | 각 bootstrap/persona API | `games.py`, sessions | `games`, sessions | |

---

## Payment

| 기능 | 상태 | 관련 화면/컴포넌트 | 관련 API | 관련 Backend 파일 | 관련 DB | 비고 |
|------|------|-------------------|----------|------------------|---------|------|
| Stripe | [ ] | — | — | — | — | SSOT/README만 |

---

## 분석 기준 파일

- `apps/api/main.py`, `apps/web-html/*.html`
- `apps/api/routes/*.py`, `apps/api/services/*.py`
- `docs/SSOT.md`, `docs/14_Code_Trace_Map.md`
