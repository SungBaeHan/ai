# ARCHITECTURE

This document describes the TRPG engine architecture for AI-driven development. It is the single reference for layers, entry points, integrations, and development rules. See also `docs/SSOT.md` for repository scope and change rules.

---

# Core Development Documents

AI agents must read the following documents before making any changes:

- docs/SSOT.md
- docs/ARCHITECTURE.md
- docs/AI_AGENT_RULES.md
- docs/DEVELOPMENT_GUIDE.md

---

# System Overview

The system is a **TRPG (Tabletop RPG) engine** backend with a FastAPI application. It provides:

- **Character, World, and Game** management (CRUD, images, AI-generated details).
- **Chat** (character/world/game sessions) and **TRPG game turns** with LLM integration.
- **RAG-style Q&A** (ask endpoint) and optional embedding/vector search.
- **User auth** (e.g. Google), **personas**, and **image assets** stored in Cloudflare R2 (S3-compatible).

The codebase follows a **clean-architecture-style** layout: domain and use cases in `src/`, adapters in `adapters/`, and the HTTP API in `apps/api/`. In practice, many API routes still call MongoDB directly instead of going through use cases; that is documented as a known issue and legacy pattern.

---

# Repository Structure

Main directories and their roles:

| Directory | Role |
|-----------|------|
| **apps/api** | FastAPI backend: `main.py`, config, startup, routes, schemas, models, dependencies, and API-level services (e.g. game session, chat persist, logging). This is the HTTP entry layer. |
| **src/domain** | Core domain entities (e.g. `Character`). Domain models and invariants; no framework or infrastructure. |
| **src/usecases** | Application use cases: character (get/list), chat (open/send_message), rag (answer_question). They depend on ports (repositories, services), not on concrete adapters. |
| **adapters** | Implementations of ports: **persistence** (MongoDB, SQLite), **external** (OpenAI/Ollama LLM, embedding), **file_storage** (R2). Adapters depend on domain/ports, not the reverse. |
| **infra** | Runtime and deployment: `docker-compose.yml`, `docker-entrypoint.sh`, nginx config. Used to run the API (e.g. uvicorn) and optional services. |

Other notable paths:

- **apps/llm/prompts** — LLM prompt definitions (e.g. TRPG game master).
- **apps/web-html** — Static HTML frontend; `js/config.js` holds `ASSET_BASE_URL` and API base.
- **docker/** — Dockerfiles and nginx for build/deploy.
- **scripts/** — Operational and migration scripts (e.g. migrate, ingest).
- **docs/** — Architecture, infra, and scratch docs; `docs/SSOT.md` is the single source of truth for repo rules.

---

# Architecture Layers

## API Layer

- **Location**: `apps/api/` (especially `main.py`, `routes/`, `schemas/`, `config.py`, `deps/`).
- **Responsibility**: HTTP entry: parse request, validate input (schemas), call use cases or (legacy) repositories/DB, format response. Handles CORS, middleware (e.g. access log), and exception handling. Should not contain business rules; it should delegate to the use case layer.

## Domain Layer

- **Location**: `src/domain/` (e.g. `character.py`).
- **Responsibility**: Core entities and domain logic. No dependencies on frameworks, DB, or external services. Defines what the application talks about (e.g. Character, fields, invariants).

## Usecase Layer

- **Location**: `src/usecases/` (character, chat, rag).
- **Responsibility**: Application workflows. Use cases depend on **ports** (interfaces in `src/ports/`) for repositories and external services, and orchestrate them. They must not depend on concrete adapters or DB drivers.

## Adapter Layer

- **Location**: `adapters/` (persistence, external, file_storage).
- **Responsibility**: Implement ports: MongoDB/SQLite repositories, OpenAI/Ollama clients, R2 storage. Translate between external APIs and domain/use-case expectations. All persistence and external I/O should go through adapters, not raw DB calls from the API.

## Infrastructure Layer

- **Location**: `infra/`, `docker/`, environment config, and the runtime that starts the app (e.g. uvicorn via `docker-entrypoint.sh`).
- **Responsibility**: Deployment, containerization, process startup, and optional sidecar services (e.g. nginx). Does not implement business logic.

---

# External Integrations

| Integration | Where it lives | Notes |
|-------------|----------------|--------|
| **MongoDB** | `adapters/persistence/mongo/` — `get_db()`, `get_client()`, repository adapters (character, chat, etc.). Index init in `apps/api/startup.py`. | Primary store. Sync (pymongo) and async (motor) both used. Env: `MONGO_URI`, `MONGO_DB_NAME`. |
| **R2 Storage** | `adapters/file_storage/r2_storage.py` — `R2Storage`, `upload_image()`. | S3-compatible (boto3). Env: `R2_ENDPOINT`/`R2_ACCOUNT_ID`, `R2_BUCKET_NAME`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. Public URL base: `ASSET_BASE_URL` or `R2_PUBLIC_BASE_URL`. |
| **LLM APIs** | `adapters/external/openai/`, `adapters/external/llm_client.py`, `adapters/external/llm_service_adapter.py`. | OpenAI Chat Completions; optional Ollama. Env: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_API_BASE`, `LLM_PROVIDER`. |
| **Stripe** | Not implemented. | Planned (e.g. subscriptions, webhooks). Referenced in `docs/SSOT.md` and related docs. |

---

# Entry Points

| Entry point | Purpose |
|-------------|----------|
| **apps/api/main.py** | FastAPI app instance. All API routes are mounted here. Run with: `uvicorn apps.api.main:app --host ... --port ...`. |
| **infra/docker-entrypoint.sh** | Production/container entry. Sets `APP_MODULE=apps.api.main:app` and runs uvicorn (default port 10000). On import failure, falls back to `apps.diag.app:app`. |

Other references:

- **Local dev**: `uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload`.
- **Render**: `render.yaml` points at root `Dockerfile` and `healthCheckPath: /health`.
- **Scripts**: `scripts/*.py` are standalone entry points (e.g. migrations, ingest); not part of the HTTP server.
- **Fallback app**: `apps/diag/app.py` — minimal FastAPI when main app fails to import.

---

# Image Asset Flow

1. **Upload**: Routes (characters, worlds, games, personas) call `get_r2_storage().upload_image(...)` in `adapters/file_storage/r2_storage.py`. Content is sent to R2 with a key prefix (e.g. `assets/char/`, `assets/world/`). The adapter returns `bucket`, `key`, `path`, and **url** (`public_base_url + "/" + key`).

2. **Public URL base**: Configured in `apps/api/config.py` as `ASSET_BASE_URL` (default `https://img.arcanaverse.ai`); env `ASSET_BASE_URL` or `R2_PUBLIC_BASE_URL`. R2Storage uses the same base for the `url` field in upload responses.

3. **URL generation for existing keys**: In `apps/api/utils/common.py`:
   - **build_public_image_url(src_file, prefix)** — builds `ASSET_BASE_URL` + `/assets/{prefix}/{filename}` (filename extracted from `src_file`). Used when serving character/world/etc. image fields.
   - **build_public_image_url_from_path(path)** — for paths like `/assets/game/xxx.png`, returns `ASSET_BASE_URL + path`.
   - **build_r2_public_url** — deprecated alias; prefer `build_public_image_url`.

4. **Serving**: Clients receive either the `url` from R2 upload responses or URLs built by the above helpers. The image list API (`GET /assets/images`) reads from the MongoDB `images` collection (or `MONGO_IMAGES_COLLECTION`) and uses `build_public_image_url(key)` when no stored URL is present.

5. **Frontend**: `apps/web-html/js/config.js` exposes `ASSET_BASE_URL` / `IMAGE_BASE`; some HTML pages set `window.__ASSET_BASE_URL__` for compatibility (e.g. when blocking r2.dev).

---

# Known Architecture Issues

- **API routes accessing MongoDB directly**  
  Most routes use `get_db()` or `get_mongo_client()` and query/update collections (characters, games, game_session, users, worlds_session, worlds_message, characters_session, characters_message, images, etc.) without going through use cases. Only `chat_v2.py` uses use cases (OpenChatUseCase, SendMessageUseCase). Character get-one and count use the repository; list, create, “my characters”, and bootstrap use direct DB. See `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md` for a full list. This is treated as **legacy**; new behavior should go through use cases.

- **Sync/async mix**  
  MongoDB is used both via sync (pymongo) and async (motor) in different places, which complicates consistency and can cause blocking in async contexts.

- **Deprecated image URL functions**  
  `build_r2_public_url` in `apps/api/utils/common.py` is deprecated; callers should use `build_public_image_url` (or `build_public_image_url_from_path` where appropriate).

- **RAG use case unused by API**  
  `src/usecases/rag/answer_question.py` exists but `apps/api/routes/ask.py` does not use it; it implements its own `retrieve_context` (Qdrant) and LLM call.

- **Duplicate env names**  
  Some options have alternate names (e.g. `MONGO_DB` vs `MONGO_DB_NAME`, `R2_BUCKET` vs `R2_BUCKET_NAME`), which can cause confusion.

---

# Future Development Rule

- **API → Usecase → Adapter**  
  New application behavior must follow: **API layer** calls a **use case**; the **use case** uses **ports** (repository/service interfaces); **adapters** implement those ports (e.g. MongoDB, R2, LLM). The API must not implement business logic or talk to the database directly for new features.

- **Direct MongoDB access from API routes is legacy**  
  Existing code that uses `get_db()` or `get_mongo_client()` in routes/deps is legacy. New code must not add new direct DB access in the API layer; it must go through use cases and adapters. When touching existing routes, prefer refactoring to use cases over adding more direct DB calls.

- **New code must use use cases**  
  New features (new endpoints, new workflows, or new domains such as worlds, games, personas, users) must be implemented by adding or extending use cases in `src/usecases/` and calling them from the API. Adapters in `adapters/` should implement the ports used by those use cases.
