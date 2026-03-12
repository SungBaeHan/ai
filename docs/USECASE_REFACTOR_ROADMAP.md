# Use Case Refactoring Roadmap

This document defines where MongoDB access should be moved from API routes into use cases, and how to execute that refactor. It does not prescribe code changes; it is a planning and guideline document. See `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md` for the detailed list of direct-access locations.

---

# Purpose

API routes should not access MongoDB directly for the following reasons.

1. **Single responsibility**  
   Routes should handle HTTP only: parse request, validate input, call application logic, format response. Persistence and domain rules belong in use cases and adapters.

2. **Testability**  
   Use cases can be tested with in-memory or fake repositories. Routes that call the database directly are harder to unit test and tie tests to a real MongoDB.

3. **Consistency**  
   Business rules (e.g. “who can create a game”, “how to compute next character id”) should live in one place. Direct DB access in routes duplicates or bypasses those rules and makes behavior inconsistent across endpoints.

4. **Maintainability**  
   Schema or storage changes (e.g. new collection, new index, migration) should be handled in adapters and use cases. If many routes talk to MongoDB directly, every change touches many files.

5. **Alignment with existing design**  
   The codebase already has `src/usecases/` and `src/ports/`; `chat_v2.py` correctly uses `OpenChatUseCase` and `SendMessageUseCase`. Moving other flows to the same pattern makes the architecture consistent and easier for humans and AI to reason about.

6. **Future development rule**  
   As stated in `docs/ARCHITECTURE.md`, new behavior must follow **API → Usecase → Adapter**. Refactoring existing routes to use cases removes legacy exceptions and sets a clear precedent.

---

# Current Situation

Most API routes and some shared dependencies access MongoDB via `get_db()` or `get_mongo_client()` instead of going through use cases.

**Routes that use use cases today**

- **chat_v2.py** — Uses `OpenChatUseCase` and `SendMessageUseCase` with `ChatRepository` (Mongo adapter). This is the target pattern.

**Routes that access MongoDB directly (to be refactored)**

| Route file | What accesses MongoDB | Collections / usage |
|------------|------------------------|----------------------|
| **games.py** | All game CRUD, session, id sequence | `games`, `game_session`; `get_next_game_id(db)` |
| **game_turn.py** | Turn execution (load session, game, update state) | `game_session`, `games` |
| **characters.py** | List (fallback), “my” list, create, bootstrap chat | `characters`, `characters_session`, `characters_message`; `get_next_character_id(db)` |
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

**Dependencies / non-route code**

| Location | What accesses MongoDB |
|----------|------------------------|
| **apps/api/deps/auth.py** | `get_current_user_from_token`, `_decode_jwt_access_token` — user lookup in `users` |
| **apps/api/main.py** | Global exception handler — `get_db()` for logging only |
| **apps/api/services/logging_service.py** | access_log, event_log, error_log — insert into log collections |

**Partial use of repository (still no use case)**

- **characters.py** — `get_one` and `get_count` use `get_character_repo()`; list, create, “my”, and bootstrap still use `get_db()` directly. Existing use cases `get_character` and `list_characters` are not called from the route.

---

# Refactoring Priority

Refactoring is grouped by impact and dependency order. Higher priority items are core to gameplay or content; lower priority are supporting or operational.

**Priority 1 (Core gameplay)**  
- **games.py** — Game creation, list, detail, session. Central to TRPG flow.  
- **game_turn.py** — Turn execution and state updates. Depends on game/session model.

Refactoring these first gives a clear “game” use case and repository boundary that other features can rely on.

**Priority 2 (Content)**  
- **characters.py** — Character list (including fallback and “my”), create, bootstrap; already has repository for get/count but not use cases.  
- **worlds.py** — World CRUD and world chat bootstrap.  
- **character_sessions.py** — Apply persona to character chat session.  
- **world_sessions.py** — Apply persona to world chat session.  
- **assets.py** — List images (metadata from MongoDB).

Content and session-persona flows are used by gameplay and chat; doing them after P1 keeps dependencies sane.

**Priority 3 (User)**  
- **user.py** — User CRUD.  
- **personas.py** — Persona CRUD (users.personas).  
- **auth.py** — Current user resolution (JWT → user).  
- **apps/api/deps/auth.py** — Same user lookup used by many routes.

User and auth are shared by most routes; refactoring them provides a single “get user” / “resolve session” use case that others can depend on.

**Priority 4 (Infrastructure)**  
- **health.py** — DB check (already uses repository; optional: add a trivial “health check” use case if desired).  
- **migrate.py** — One-off migration endpoint; can remain operational or use a dedicated “migrate” use case.  
- **apps/api/services/logging_service.py** — Log writes; can stay as-is or go through a “write log” use case.  
- **apps/api/main.py** — Exception handler DB usage is logging-only; low priority.

These are operational or cross-cutting; refactor after core and content flows.

---

# Refactoring Strategy

**Current pattern (legacy)**  
- **Route → MongoDB**  
  The route receives `db = Depends(get_db)` or calls `get_mongo_client()`, then uses `db.collection.find_one()`, `insert_one()`, etc. Business logic (e.g. “next id”, “who can create”) lives in the route or in helpers that take `db`.

**Target pattern**  
- **Route → Usecase → Adapter**  
  1. **Route** — Validates request (schemas), extracts auth/session, calls a use case with simple arguments (ids, DTOs). No `get_db()` or `get_mongo_client()` in the route.  
  2. **Usecase** — Implements the workflow: validate, call repository/service ports (e.g. `GameRepository`, `UserRepository`), return a result. No knowledge of MongoDB or FastAPI.  
  3. **Adapter** — Implements the port (e.g. `MongoGameRepository`) and uses `get_db()` or a Mongo client. All MongoDB access is inside adapters.

**How to convert a route**

1. **Define or reuse a port** (in `src/ports/repositories/` or `src/ports/services/`). The port is an interface: e.g. `get_by_id(id)`, `save(game)`, `list_for_user(user_id)`.  
2. **Implement or reuse an adapter** (in `adapters/persistence/mongo/` or elsewhere). The adapter implements the port and performs all Mongo operations.  
3. **Add or extend a use case** (in `src/usecases/`). The use case takes the port(s) in its constructor, implements the workflow (e.g. “load game, check ownership, update turn, save”), and returns a result DTO or domain object.  
4. **Change the route** to instantiate the adapter (or receive it via dependency injection), construct the use case with that adapter, call the use case with request data, and map the result to the HTTP response. Remove all direct `get_db()` / `get_mongo_client()` and collection access from the route.  
5. **Test** the use case with a fake in-memory implementation of the port; keep or add integration tests for the adapter and the route as needed.

**Example (conceptual)**  
- **Before**: Route `POST /v1/games` receives `db`, calls `get_next_game_id(db)`, builds a doc, `db.games.insert_one(doc)`, then updates `game_session`.  
- **After**: Route calls `CreateGameUseCase(repo=game_repo, session_repo=session_repo).execute(meta, user_id)`. The use case uses the repos to get next id, create game, create/update session; the route only maps the use case result to `GameResponse`.

---

# Migration Guidelines

Use these rules when refactoring or adding features. No code is prescribed here; these are constraints for future work.

1. **One route, one use case (per operation)**  
   Each meaningful operation (e.g. “create game”, “list my characters”, “apply persona to session”) should be implemented by a single use case. The route’s job is to call that use case and translate input/output.

2. **No new direct DB access in routes**  
   When adding or changing behavior, do not introduce new `get_db()` or `get_mongo_client()` in `apps/api/routes/` or in `apps/api/deps/`. Add or extend a use case and an adapter instead.

3. **Ports in src/ports, adapters in adapters/**  
   Define interfaces (ports) under `src/ports/`. Implement them under `adapters/` (e.g. `adapters/persistence/mongo/`). Use cases live in `src/usecases/` and depend only on ports.

4. **Prefer reusing existing use cases**  
   If a route currently does “list characters” with direct DB, refactor it to call the existing `list_characters` use case (and extend the port/adapter if the current API needs something the use case does not yet support) rather than inventing a second path to the same data.

5. **Auth and “current user”**  
   When refactoring auth, introduce a single use case (e.g. “resolve user from token”) used by `deps/auth.py` and possibly by routes. The adapter for that use case performs the `users` lookup. Other use cases that need “current user” should receive a user id or DTO from the route, not a DB handle.

6. **Id generation and sequences**  
   “Next id” logic (e.g. `get_next_character_id`, `get_next_game_id`) belongs in the adapter or in a use case that uses the repository (e.g. repository method `next_id()` or use case that asks repository for “max id” and increments). Routes must not query the DB for sequences.

7. **Bootstrap and session-persona**  
   Chat bootstrap (load session + messages) and “apply persona to session” are good candidates for dedicated use cases (e.g. `BootstrapCharacterChat`, `ApplyPersonaToCharacterSession`) with session/message repositories. Routes then become thin callers.

8. **Operational endpoints**  
   For health and migrate, either keep minimal direct or repository-only access with a comment that they are operational, or add a small use case (e.g. `CheckDbHealth`, `RunMigration`) for consistency. Document the choice.

9. **Logging and cross-cutting concerns**  
   Logging service that writes to MongoDB can remain as-is during the first waves of refactor, or later be wrapped in a “write access/event/error log” use case if the team wants all DB writes to go through use cases.

10. **Reference**  
    Use `docs/ARCHITECTURE.md` for the overall rule (“API → Usecase → Adapter”) and `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md` for the exact list of routes and collections to migrate. This roadmap defines the order and strategy; it does not replace the SSOT or the architecture doc.
