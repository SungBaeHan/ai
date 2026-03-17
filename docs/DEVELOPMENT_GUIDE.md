# Development Guide for AI Agents

This guide is for AI agents (Cursor, Codex, etc.) working on this repository. It summarizes workflow, architecture, and safety rules. When in doubt, the referenced documents are authoritative.

---

# Development Workflow

**GitHub Issue → Branch → PR**

1. **Start from a GitHub Issue**  
   All work must be driven by a single GitHub Issue. The issue description is the source of requirements. Do not implement features or fixes that are not described in the issue.

2. **Create a branch**  
   One issue = one branch. Name the branch after the issue (e.g. `fix/123-image-url`, `feature/456-game-turn`). Do not combine multiple issues in one branch.

3. **Implement and open a Pull Request**  
   Implement only what the issue asks for. Open a PR that references the issue. Keep the PR scope minimal and reviewable.

4. **Verification**  
   After implementation, provide a short summary and verification steps (see Ticket Implementation Flow below). Ensure the API runs and main flows are not broken.

---

# Architecture Rules

- **API routes must not access MongoDB directly.**  
  New behavior must go through use cases and adapters. Routes handle HTTP only: parse request, validate input, call a use case (or legacy repository where refactor has not yet been done), and format response. Do not add new `get_db()` or `get_mongo_client()` in routes. See `docs/ARCHITECTURE.md` and `docs/USECASE_REFACTOR_ROADMAP.md`.

- **Usecases must contain business logic.**  
  Workflows (e.g. "create game", "list my characters", "apply persona to session") belong in `src/usecases/`. Use cases depend on ports (interfaces in `src/ports/`), not on concrete DB or HTTP. They orchestrate repositories and services and enforce rules.

- **Adapters handle external systems.**  
  All persistence (MongoDB, SQLite), external APIs (OpenAI, R2), and other I/O live in `adapters/`. Adapters implement the ports used by use cases. Do not put DB connection or external API calls in routes or domain.

---

# AI Development Rules

AI agents **must** follow these documents:

| Document | Role |
|----------|------|
| **docs/SSOT.md** | Single source of truth for repo scope, directory roles, change rules, env/secrets, and ticket-based development. Conflicts with other docs are resolved in favor of SSOT. |
| **docs/ARCHITECTURE.md** | Layers (API, domain, usecase, adapter, infra), entry points, external integrations, image asset flow, known issues, and the rule: **API → Usecase → Adapter**. |
| **docs/AI_AGENT_RULES.md** | Detailed rules for AI agents: issue-driven development, minimal changes, no refactors outside scope, no DB schema/infra/env changes unless requested, API stability, logging, testing, and when to stop and ask for clarification. |

Before changing code:

1. Read the issue and the relevant sections of the three documents above.
2. Confirm the change is within the issue scope and does not violate SSOT or architecture rules.
3. If the issue implies architecture, database schema, or infrastructure changes, stop and request clarification unless the issue explicitly requests them.

---

# Ticket Implementation Flow

1. **Read the issue**  
   Understand the goal, acceptance criteria, and any constraints. Treat the issue text as the single source of requirements for that ticket.

2. **Identify modules**  
   Determine which parts of the codebase are affected: routes, use cases, adapters, schemas, config. Use `docs/ARCHITECTURE.md` and `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md` to find where logic and DB access live.

3. **Create an implementation plan**  
   List concrete steps (e.g. "add use case X", "call use case from route Y", "extend adapter Z"). Prefer minimal changes and existing patterns. Do not refactor unrelated code.

4. **Implement minimal changes**  
   Change only what is needed to satisfy the issue. Reuse existing patterns and layers. Do not rename folders, restructure the repo, or modify unrelated files.

5. **Provide verification steps**  
   After implementation, output a short summary with:
   - **Files modified** (paths).
   - **Key changes** (what was done).
   - **Verification steps** (how to confirm the fix or feature works).
   - **Remaining risks** (if any), e.g. legacy behavior or edge cases.

---

# Code Safety Rules

**Avoid:**

- **Large refactors** — Do not rewrite or refactor modules that are outside the issue scope. Prefer small, targeted edits.
- **Folder restructuring** — Do not move or rename top-level directories (e.g. `apps/`, `src/`, `adapters/`) unless the issue explicitly asks for it.
- **Database schema changes** — Do not add, remove, or rename collections or fields unless the issue explicitly requires it. Do not add migration scripts without an explicit request.
- **Infra changes** — Do not change Dockerfiles, docker-compose, nginx config, Render config, or environment variable names unless the issue explicitly requires it.

If the issue implies any of the above, **stop and request clarification** before proceeding. Do not guess.

---

# Preferred Patterns

**Route → Usecase → Adapter**

- **Route** — Validates request, extracts auth/session, calls a use case with simple arguments, maps result to HTTP response. No business logic, no direct DB or external API calls.
- **Usecase** — Implements the workflow using only ports (repositories, services). Contains business rules and orchestration.
- **Adapter** — Implements ports: MongoDB, R2, LLM clients, etc. All I/O and external system details stay here.

For **new features**, always add or extend a use case and an adapter; have the route call the use case. Do not add new direct MongoDB access in routes. See `docs/USECASE_REFACTOR_ROADMAP.md` for migration strategy.

---

# Legacy Code

Some existing routes access MongoDB directly.

This is considered legacy behavior.

New features and bug fixes must avoid this pattern and instead use the following structure:

Route → Usecase → Adapter

Details: Direct DB access is documented in `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md` and in the "Known Architecture Issues" section of `docs/ARCHITECTURE.md`. When modifying legacy routes without refactoring, do not add new direct DB access. When the issue explicitly asks to move a route to use cases, follow `docs/USECASE_REFACTOR_ROADMAP.md`.

---

# Ticket Workflow: Analysis vs Scratch

- **Formal root-cause / implementation-plan documents** → **docs/analysis/** (ticket-linked; e.g. BUG-NNN_short_name_analysis.md).
- **Temporary debug notes / experiments** → **docs/scratch/** (non-canonical; may be promoted later to docs/analysis/ or docs/architecture/ if they become long-term reference).
- **Documentation structure changes** (new folders, moving canonical docs) are **out of scope** for normal ticket work. Do not change docs folder structure during ticket implementation. See docs/SSOT.md (Documentation Structure Lock).

---

# Summary

| Do | Don't |
|----|--------|
| One issue → one branch → one PR | Multiple issues in one PR |
| Read SSOT, ARCHITECTURE, AI_AGENT_RULES before coding | Assume or invent requirements |
| Minimal, issue-scoped changes | Large refactors, folder moves |
| New features via usecase + adapter | New direct MongoDB in routes |
| Provide verification steps and summary | Change DB schema, infra, or env without explicit issue request |
| Stop and ask when unsure about architecture/DB/infra | Guess or proceed without clarification |
