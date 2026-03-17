# Repository Structure Analysis Report

**Generated:** 2025-03-13  
**Scope:** Full repository structure (depth 4), `docs/` inventory, classification, and structural assessment.  
**No files were modified;** this is a documentation-only report.

---

## 1. Directory Tree (Depth 4)

```
f:\git\ai\
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── .vscode/
├── __pycache__/
├── _volumes/
│   ├── ollama_models/
│   │   └── models/
│   ├── qdrant/
│   └── qdrant_storage/
│       ├── aliases/
│       └── collections/
├── adapters/
│   ├── external/
│   │   ├── embedding/
│   │   └── openai/
│   ├── file_storage/
│   └── persistence/
│       ├── mongo/
│       └── sqlite/
├── apps/
│   ├── api/
│   │   ├── core/
│   │   ├── dependencies/
│   │   ├── deps/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── core/
│   │   └── utils/
│   ├── diag/
│   ├── llm/
│   │   └── prompts/
│   └── web-html/
│       ├── create/
│       ├── js/
│       └── static/
│           └── js/
├── assets/
│   ├── char/
│   ├── img/
│   ├── persona/
│   └── temp/
├── data/
│   ├── db/
│   └── json/
├── docker/
├── docker_img/
│   └── DockerDesktopWSL/
├── docs/
│   ├── analysis/
│   ├── architecture/
│   ├── infra/
│   ├── logs/
│   ├── misc/
│   ├── scratch/
│   └── tickets/
│       └── MS-01/
├── html/
│   └── app/
│       └── web/
│           └── src/
│               └── pages/
├── infra/
│   └── nginx/
│       └── conf.d/
├── packages/
│   ├── db/
│   └── rag/
├── pem/
├── scripts/
│   └── data/
├── src/
│   ├── domain/
│   ├── ports/
│   │   ├── repositories/
│   │   └── services/
│   └── usecases/
│       ├── character/
│       ├── chat/
│       └── rag/
├── tests/
└── tmp/
```

*Note: Only directories are shown. `__pycache__` and similar build/cache dirs are omitted from depth-4 expansion where redundant.*

---

## 2. Important Folders

### 2.1 `apps/`

Application layer. Contains:

- **`apps/api/`** — FastAPI backend: `main.py`, `bootstrap.py`, `config.py`, `startup.py`; `routes/` (characters, worlds, games, chat, auth, game_turn, etc.); `schemas/`, `models/`, `dependencies/`, `deps/`, `services/`, `utils/`, `core/`. Primary HTTP entry point.
- **`apps/core/`** — Shared app utilities (e.g. `utils/assets.py`).
- **`apps/diag/`** — Diagnostic/small tooling app.
- **`apps/llm/`** — LLM-related code; **`prompts/`** holds prompt definitions (e.g. TRPG game master).
- **`apps/web-html/`** — Static HTML frontend: `index.html`, `home.html`, `chat.html`, `game.html`, `world.html`, `my.html`, `personas.html`, `search.html`; `create/` (character, world, game); `js/`, `static/js/`.

### 2.2 `src/`

Clean-architecture core (domain, ports, use cases):

- **`src/domain/`** — Domain entities (e.g. `Character`).
- **`src/ports/`** — Interfaces: `repositories/` (character, chat), `services/` (LLM, embedding).
- **`src/usecases/`** — Application logic: `character/` (get, list), `chat/` (open, send_message), `rag/` (answer_question).

Target rule: **API → Usecase → Adapter**; many routes still use MongoDB directly (legacy).

### 2.3 `adapters/`

Implementations of ports and external integrations:

- **`adapters/persistence/`** — MongoDB (`mongo/`) and SQLite (`sqlite/`) repositories.
- **`adapters/external/`** — LLM clients, OpenAI client, **embedding** (sentence transformer).
- **`adapters/file_storage/`** — R2 (S3-compatible) storage.

### 2.4 `infra/`

Runtime and deployment:

- **`infra/`** — `docker-compose.yml`, `docker-entrypoint.sh`, `ollama-entrypoint.sh`, reverse-proxy compose, `README-OPERATIONS.md`, `README-reverse-proxy.md`.
- **`infra/nginx/conf.d/`** — Nginx config (e.g. `api.arcanaverse.ai.conf`).

### 2.5 `docs/`

All project documentation:

- **Root** — SSOT, architecture, AI rules, dev guide, quick start, entrypoints, refactor roadmap.
- **`docs/architecture/`** — Directory/file structure, refactoring summary.
- **`docs/analysis/`** — Bug/feature analysis reports (e.g. BUG-003).
- **`docs/infra/`** — Infra/setup guides (e.g. Google Login).
- **`docs/logs/`** — Dated work logs.
- **`docs/misc/`** — Miscellaneous (e.g. unused features).
- **`docs/scratch/`** — Scratch/temporary and deep-dive notes (debug, audits, samples).
- **`docs/tickets/`** — Ticket system: README, template, OrderForm, milestone subfolders (e.g. `MS-01/`).

---

## 3. Documentation Inventory (`docs/`)

### 3.1 Root-level (`docs/*.md`)

| File | Purpose |
|------|--------|
| **README.md** | Docs hub: architecture overview, ticket system, refactor roadmap, scratch/infra pointers, recommended reading order (SSOT → ARCHITECTURE → AI_AGENT_RULES → DEVELOPMENT_GUIDE → AI_DEV_PROMPT). |
| **SSOT.md** | Single source of truth: repo scope, entry points, directory roles, env/secrets, change rules, ticket-based workflow. Overrides other docs on conflict. |
| **ARCHITECTURE.md** | System architecture: layers (API, domain, usecase, adapter, infra), integrations, image flow, known issues, rule “API → Usecase → Adapter”. |
| **AI_AGENT_RULES.md** | Rules for AI agents: source of truth, scope, issue-driven dev, safety (no unrelated refactors, no schema/infra changes unless requested). |
| **AI_ENTRYPOINT.md** | First document for AI agents: read SSOT → ARCHITECTURE → AI_AGENT_RULES → DEVELOPMENT_GUIDE, then the assigned ticket. |
| **AI_DEV_PROMPT.md** | Standard execution prompt for AI (Cursor/Codex): same reading order + ticket-based implementation. |
| **DEVELOPMENT_GUIDE.md** | Dev workflow (Issue → Branch → PR), architecture rules, AI rules, ticket flow, references to ARCHITECTURE and scratch. |
| **QUICK_START.md** | Quick start: Docker Compose, Ollama, endpoints, basic commands. |
| **USECASE_REFACTOR_ROADMAP.md** | Plan to move MongoDB access from routes to use cases; references `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md`. |

### 3.2 `docs/architecture/`

| File | Purpose |
|------|--------|
| **DIRECTORY_STRUCTURE.md** | Snapshot of repo directory layout (Korean, dated 2025-01-27). |
| **CURRENT_FILE_STRUCTURE.md** | Current file structure with roles (apps/api, web-html, src, adapters). |
| **REFACTORING_SUMMARY.md** | Summary of refactors: packages → adapters, clean-architecture layers. |

### 3.3 `docs/analysis/`

| File | Purpose |
|------|--------|
| **BUG-003-persona-not-rendered-in-new-chat-analysis.md** | Analysis for BUG-003: root cause, files, working vs broken flow, implementation plan (no code changes). |

### 3.4 `docs/infra/`

| File | Purpose |
|------|--------|
| **GOOGLE_LOGIN_SETUP.md** | Step-by-step Google OAuth / Google Login setup (Console, frontend `my.html`). |

### 3.5 `docs/logs/`

| File | Purpose |
|------|--------|
| **2025-01-27.md**, **2025-11-05.md**, **2025-11-07.md**, **2025-11-19.md**, **2025-11-21.md**, **2025-11-24.md**, **2025-11-25.md**, **2025-12-03.md**, **2025-12-04.md** | Dated work logs (what was done, commits, decisions). |

### 3.6 `docs/misc/`

| File | Purpose |
|------|--------|
| **UNUSED_FEATURES.md** | List of unused API endpoints and scripts, with recommendations. |

### 3.7 `docs/scratch/`

Temporary, debug, and deep-dive notes. Referenced by ARCHITECTURE, DEVELOPMENT_GUIDE, USECASE_REFACTOR_ROADMAP.

| File | Purpose (inferred) |
|------|--------------------|
| **ARCHITECTURE_OVERVIEW.md** | Repository structure and architecture overview. |
| **ROUTES_DIRECT_MONGO_ACCESS.md** | List of routes/collections with direct MongoDB access (refactor list). |
| **SEARCH_R2_DEV_DOMAIN.md** | Search for `r2.dev` / pub-*.r2.dev usage. |
| **VERIFICATION_ASSET_URL_PREFIX.md** | Asset URL prefix verification. |
| **BUG-002_FINAL_SUMMARY.md** | BUG-002 final summary (frontend-only fix). |
| **BUG-002_FRONTEND_COMMIT_RENDER_PATH.md** | BUG-002 frontend commit/render path analysis. |
| **modal_infinite_debug_context.md** | Modal infinite-scroll debug context. |
| **bugfix_modal_infinite_append.md** | Modal infinite append bugfix notes. |
| **ux_infinite_skeleton*.md** (multiple) | UX/skeleton notes for infinite scroll (search, create game, home character). |
| **current_repo_structure.md** | Snapshot of repo structure. |
| **LOG_PATH_MAP.md** | Log path mapping. |
| **game_chat_badge_render_audit.md** | Game chat badge render audit. |
| **DIAGNOSIS_REPORT.md** | Generic diagnosis report. |
| **world_chat_tree.md** | World chat structure/tree. |
| **MongoSample.md**, **Sample.md** | Sample data/structure. |
| **SOLUTION_STRUCTURE.md**, **SOLUTION_MAP.md** | Solution structure/map. |

### 3.8 `docs/tickets/`

| File | Purpose |
|------|--------|
| **README.md** | Ticket system: location (`docs/tickets/`), workflow, naming (TYPE-ID_short_description.md), structure (Problem, Context, Scope, Strategy, Acceptance, Verification). |
| **_TEMPLATE.md** | Template for new tickets. |
| **OrderForm.md** | Short “order” prompts: BUG/FEATURE/TASK + pointer to AI_DEV_PROMPT and ticket path. |
| **MS-01/BUG-001_character_cdn.md** | Ticket: character CDN. |
| **MS-01/BUG-002_game_character_selection_not_applied.md** | Ticket: game character selection not applied. |
| **MS-01/BUG-003 Persona Not Rendered in New Chat Sessions.md** | Ticket: persona not rendered in new chat sessions. |

---

## 4. Documentation Classification

### 4.1 Architecture-related

- **Primary:** `docs/ARCHITECTURE.md`, `docs/SSOT.md`
- **Supporting:** `docs/architecture/DIRECTORY_STRUCTURE.md`, `docs/architecture/CURRENT_FILE_STRUCTURE.md`, `docs/architecture/REFACTORING_SUMMARY.md`
- **Scratch/overlap:** `docs/scratch/ARCHITECTURE_OVERVIEW.md`, `docs/scratch/current_repo_structure.md`, `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md`

### 4.2 Ticket-related

- **Process:** `docs/tickets/README.md`, `docs/tickets/_TEMPLATE.md`, `docs/tickets/OrderForm.md`
- **Tickets:** `docs/tickets/MS-01/BUG-001_character_cdn.md`, `docs/tickets/MS-01/BUG-002_game_character_selection_not_applied.md`, `docs/tickets/MS-01/BUG-003 Persona Not Rendered in New Chat Sessions.md`

### 4.3 Analysis documents

- **Formal analysis:** `docs/analysis/BUG-003-persona-not-rendered-in-new-chat-analysis.md`
- **Scratch analysis:** e.g. `docs/scratch/BUG-002_FINAL_SUMMARY.md`, `docs/scratch/BUG-002_FRONTEND_COMMIT_RENDER_PATH.md`, `docs/scratch/DIAGNOSIS_REPORT.md`, `docs/scratch/game_chat_badge_render_audit.md`

### 4.4 Prompts (AI / execution)

- **Entrypoints/prompts:** `docs/AI_ENTRYPOINT.md`, `docs/AI_DEV_PROMPT.md`
- **OrderForm:** `docs/tickets/OrderForm.md` (short prompts pointing to ticket + AI_DEV_PROMPT)
- **LLM prompts (code):** `apps/llm/prompts/` (e.g. TRPG game master) — not under `docs/`.

### 4.5 Scratch / temp

- **Location:** `docs/scratch/`
- **Content:** Debug context, BUG-002 summaries, R2/asset checks, infinite-scroll/UX notes, repo structure snapshots, sample data, solution maps, route/Mongo list. Some are referenced by ARCHITECTURE and USECASE_REFACTOR_ROADMAP (e.g. `ROUTES_DIRECT_MONGO_ACCESS.md`).

---

## 5. Structural Problems

### 5.1 Duplicated / overlapping documentation

- **Directory structure** is described in several places: `docs/ARCHITECTURE.md`, `docs/architecture/DIRECTORY_STRUCTURE.md`, `docs/architecture/CURRENT_FILE_STRUCTURE.md`, `docs/scratch/ARCHITECTURE_OVERVIEW.md`, `docs/scratch/current_repo_structure.md`. Risk of drift and conflicting snapshots.
- **Architecture overview** exists both in root (`ARCHITECTURE.md`) and scratch (`ARCHITECTURE_OVERVIEW.md`); roles are unclear (which is canonical).

### 5.2 Unclear responsibilities

- **`docs/architecture/` vs `docs/ARCHITECTURE.md`:** One is the main architecture doc; the other holds structure snapshots and refactor summary. The relationship (canonical vs historical) is not stated.
- **`docs/analysis/` vs `docs/scratch/`:** Analysis is for formal, ticket-linked reports; scratch is for temporary/debug. Some BUG-002 analysis lives in scratch (e.g. BUG-002_FINAL_SUMMARY) rather than under `analysis/`, so the boundary is inconsistent.
- **AI reading order** is given in both `AI_ENTRYPOINT.md` and `AI_DEV_PROMPT.md` with slight differences (e.g. AI_ENTRYPOINT vs AI_DEV_PROMPT as step 1); no single canonical sequence.

### 5.3 Scattered architecture definitions

- **Layers and rules:** Mainly in `ARCHITECTURE.md` and `DEVELOPMENT_GUIDE.md`; references to scratch (e.g. `ROUTES_DIRECT_MONGO_ACCESS.md`) for details. Refactor strategy is in `USECASE_REFACTOR_ROADMAP.md`. So “architecture” is split across root, architecture/, and scratch.
- **Repo structure:** SSOT, ARCHITECTURE, architecture/*, and scratch all describe or snapshot structure; no single “one place” for the current tree.

### 5.4 Mixed analysis / ticket content

- **Tickets** (e.g. BUG-003) contain Problem, Context, Scope, Strategy, Acceptance, Verification — and sometimes implementation hints. Formal **analysis** (root cause, files, plan) is in `docs/analysis/`. For BUG-002, analysis stayed in scratch; for BUG-003 it’s in analysis. Inconsistent pattern.
- **Scratch** contains ticket-related summaries (e.g. BUG-002_FINAL_SUMMARY) that could be considered analysis outputs; no clear rule that “analysis for ticket X” lives under `docs/analysis/`.

### 5.5 Referenced but possibly missing or fragile

- **`docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md`** is referenced by USECASE_REFACTOR_ROADMAP, DEVELOPMENT_GUIDE, and ARCHITECTURE. If it is removed or renamed, those references break.
- **Scratch** is described as temporary; important refactor data (e.g. ROUTES_DIRECT_MONGO_ACCESS) lives there, so long-term stability of that content is unclear.

### 5.6 Naming and placement

- **Spaces in filenames:** e.g. `BUG-003 Persona Not Rendered in New Chat Sessions.md` — can cause issues in tooling or URLs; ticket naming convention in README uses underscores.
- **OrderForm.md** is in `tickets/` but works as a prompt/order form rather than a ticket; placement is a bit ambiguous.

---

## 6. Suggestions for Improvement

1. **Single canonical structure doc**  
   - Choose one place for “current directory tree” (e.g. `docs/architecture/` or SSOT) and one for “current file/structure snapshot.”  
   - Deprecate or clearly mark others as historical (e.g. “Snapshot as of YYYY-MM-DD”) and link to the canonical doc.

2. **Clarify architecture vs scratch**  
   - State that `docs/ARCHITECTURE.md` is the canonical architecture doc.  
   - Either move `docs/scratch/ARCHITECTURE_OVERVIEW.md` into `docs/architecture/` as a supplement or remove/redirect it to avoid two “overviews.”

3. **Stabilize refactor-critical scratch docs**  
   - Move or copy `ROUTES_DIRECT_MONGO_ACCESS.md` to a permanent location (e.g. `docs/architecture/` or `docs/refactoring/`) and update references in ARCHITECTURE, DEVELOPMENT_GUIDE, USECASE_REFACTOR_ROADMAP.  
   - Keep scratch for truly temporary notes only.

4. **Consistent analysis location**  
   - Adopt a rule: “Analysis for ticket X (root cause, files, implementation plan) lives in `docs/analysis/` with a clear name (e.g. `BUG-NNN-short-name-analysis.md`).”  
   - Move or copy important BUG-002 analysis from scratch to `docs/analysis/` if still relevant, or mark scratch copies as superseded.

5. **Single AI reading order**  
   - Define the canonical sequence in one place (e.g. SSOT or AI_ENTRYPOINT) and have AI_DEV_PROMPT and DEVELOPMENT_GUIDE reference it (e.g. “See docs/AI_ENTRYPOINT.md for reading order”) to avoid divergence.

6. **Ticket naming**  
   - Use underscores in ticket filenames (e.g. `BUG-003_persona_not_rendered_in_new_chat_sessions.md`) to match `docs/tickets/README.md` and avoid spaces in paths.

7. **OrderForm placement**  
   - Consider moving `OrderForm.md` to `docs/` root or a `docs/prompts/` folder if it is primarily an AI prompt, and keep `docs/tickets/` for tickets and ticket process only.

8. **Scratch policy**  
   - Add a short `docs/scratch/README.md`: purpose (temporary/debug), that referenced files (e.g. ROUTES_DIRECT_MONGO_ACCESS) may be promoted to architecture/, and that important conclusions should be moved to analysis/ or architecture/ when stable.

---

## 7. Report Summary

| Section | Content |
|--------|--------|
| **Directory tree** | Depth-4 tree of repository (Section 1). |
| **Major folders** | apps, src, adapters, infra, docs explained (Section 2). |
| **Docs inventory** | All listed files under `docs/` with purpose (Section 3). |
| **Classification** | Architecture, tickets, analysis, prompts, scratch/temp (Section 4). |
| **Structural issues** | Duplication, unclear ownership, scattered architecture, mixed analysis/ticket content, fragile references, naming (Section 5). |
| **Suggestions** | Single structure doc, clarify architecture vs scratch, stabilize refactor docs, consistent analysis location, single AI reading order, ticket naming, OrderForm placement, scratch policy (Section 6). |

This report is for analysis only; no repository files were modified.
