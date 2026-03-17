# Routes and Code with Direct MongoDB Access

This document lists API routes and other code that access MongoDB directly instead of going through use cases. It is the reference for refactoring; see docs/USECASE_REFACTOR_ROADMAP.md for strategy and priority. For canonical architecture rules, see docs/SSOT.md and docs/ARCHITECTURE.md.

---

## Routes that use use cases today

- **chat_v2.py** — Uses `OpenChatUseCase` and `SendMessageUseCase` with `ChatRepository` (Mongo adapter). This is the target pattern.

---

## Routes that access MongoDB directly (to be refactored)

| Route file | What accesses MongoDB | Collections / usage |
|------------|------------------------|----------------------|
| **games.py** | All game CRUD, session, id sequence | `games`, `game_session`; `get_next_game_id(db)` |
| **game_turn.py** | Turn execution (load session, game, update state) | `game_session`, `games` |
| **characters.py** | List (fallback), "my" list, create, bootstrap chat | `characters`, `characters_session`, `characters_message`; `get_next_character_id(db)` |
| **worlds.py** | World CRUD, bootstrap chat | `worlds` (if present), `worlds_session`, `worlds_message` |
| **character_sessions.py** | Apply persona to character session | `characters_session`, `users` |
| **world_sessions.py** | Apply persona to world session | `worlds_session`, `users` |
| **assets.py** | List image metadata | `images` (or `MONGO_IMAGES_COLLECTION`) |
| **user.py** | User CRUD | `users` |
| **personas.py** | Persona CRUD (embedded in user doc) | `users` (personas array) |
| **auth.py** | Resolve current user from JWT | `users` |
| **app_chat.py** | Logging, session/persona lookup for TRPG chat | `get_db()` for log context; `characters_session` via `get_mongo_client()` |
| **health.py** | DB connectivity check | Uses `MongoCharacterRepository` (adapter), not a use case |
| **migrate.py** | SQLite → Mongo migration | `get_db()`, `characters` |

---

## Dependencies / non-route code

| Location | What accesses MongoDB |
|----------|------------------------|
| **apps/api/deps/auth.py** | `get_current_user_from_token`, `_decode_jwt_access_token` — user lookup in `users` |
| **apps/api/main.py** | Global exception handler — `get_db()` for logging only |
| **apps/api/services/logging_service.py** | access_log, event_log, error_log — insert into log collections |

---

## Partial use of repository (still no use case)

- **characters.py** — `get_one` and `get_count` use `get_character_repo()`; list, create, "my", and bootstrap still use `get_db()` directly. Existing use cases `get_character` and `list_characters` are not called from the route.
