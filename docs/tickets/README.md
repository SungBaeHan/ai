# Ticket System

Arcanaverse uses a **ticket-driven development workflow**.

All development tasks are defined as Markdown tickets.

Location:

docs/tickets/

Example:

docs/tickets/MS-01/BUG-001_character_cdn.md

---

# Ticket Workflow

Development flow:

Ticket → Cursor → Implementation → PR → Verification

Steps:

1. Create ticket
2. Cursor reads ticket
3. Cursor proposes implementation plan
4. Implementation
5. Verification
6. Pull Request

---

# Ticket vs Analysis vs Scratch

- **Ticket** (docs/tickets/) — Task definition: problem, scope, acceptance criteria, verification. One ticket = one branch = one PR.
- **Analysis** (docs/analysis/) — Formal ticket-linked documents: root-cause analysis, implementation plan. Name e.g. `BUG-NNN_short_name_analysis.md`.
- **Scratch** (docs/scratch/) — Temporary notes, debug context, experiments. Non-canonical; promote to docs/analysis/ or docs/architecture/ when they become long-term reference.

For **ticket completion**, **report rules**, and **Definition of Done**, refer to:
- [docs/QA_AND_DONE.md](../QA_AND_DONE.md)
- [docs/analysis/README.md](../analysis/README.md)

---

# Ticket Naming

Ticket files should follow this naming format:

TYPE-ID_short_description.md

Use **underscores** for multi-word descriptions (no spaces in filenames).

Examples:

BUG-001_character_cdn.md
BUG-003_persona_not_rendered_in_new_chat_sessions.md
TASK-002_remove_deprecated_helpers.md
FEAT-010_myfavorite_api.md

---

# Ticket Structure

All tickets should follow the same structure.

Problem
Context
Scope
Strategy
Acceptance
Verification

---

# Problem

Describe the issue clearly.

Example:

Character images are currently served from the R2 public domain.

Current:
https://pub-xxx.r2.dev/assets/char/123.png

Expected:
https://img.arcanaverse.ai/assets/char/123.png


---

# Context

Provide technical context.

Include:

- relevant modules
- configuration
- architecture hints

Example:

apps/api/utils/common.py
apps/api/config.py
adapters/file_storage/r2_storage.py

---

# Scope

Define what the ticket is allowed to change.

Example:

Allowed:

- update URL generation logic

Not allowed:

- database schema changes
- infrastructure changes
- unrelated refactors

---

# Strategy

Provide an implementation hint.

Example:

Use ASSET_BASE_URL as canonical asset domain.
Rewrite r2.dev URLs to CDN domain.

---

# Acceptance Criteria

Define when the ticket is complete.

Example:

1 Character image URLs must start with:

https://img.arcanaverse.ai

2 API responses must not contain r2.dev.

3 Existing functionality must remain unchanged.

---

# Verification

Provide manual verification steps.

Example:

1 Start API
2 Open character list
3 Inspect image URL
4 Confirm CDN domain is used

---

# Ticket Size Rule

Tickets should be small and focused.

A ticket should typically modify:

1–3 files
a single logical change

---

# AI Output Format

Before coding AI should provide:

root cause
files to modify
implementation plan

After coding AI should provide:

files changed
summary
verification steps
potential risks

---

# Architecture Rule

All new code must follow:

API Route → Usecase → Adapter

Direct MongoDB access from API routes is **legacy**.

---

# Important Rule

One ticket should produce:

1 branch
1 pull request

---

# Development Philosophy

Arcanaverse follows **AI-native development** principles.

SSOT
Architecture-first
Ticket-driven development
AI-assisted implementation

---

All tickets must follow the structure defined in _TEMPLATE.md.