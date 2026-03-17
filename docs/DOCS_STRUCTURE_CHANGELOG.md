# Documentation Structure Changelog

This document summarizes the documentation structure stabilization performed so that "AI/people know where to read first" and doc roles are clear. No code, infra, or schema changes were made; only docs/ was updated.

---

## What changed

1. **docs/SSOT.md**
   - Added **Canonical Documentation**: which docs are top-level (SSOT, ARCHITECTURE, AI_ENTRYPOINT, AI_AGENT_RULES, DEVELOPMENT_GUIDE); docs/architecture/ and docs/scratch/ defined as supporting/temporary.
   - Added **AI Reading Order** (single canonical sequence): SSOT → ARCHITECTURE → AI_AGENT_RULES → DEVELOPMENT_GUIDE → AI_ENTRYPOINT → ticket → analysis.
   - Added **Documentation Structure Lock**: allowed (tickets, analysis, scratch updates); not allowed (new doc systems/folders, structure changes during normal ticket work); structural changes only in dedicated doc sessions.

2. **docs/AI_ENTRYPOINT.md**
   - Reading order aligned with SSOT (including steps 6–7: ticket, analysis).
   - Added rule: during ticket work, do not propose or create new documentation systems or folder structures; follow existing layout.

3. **docs/AI_AGENT_RULES.md**
   - Added **§16 Documentation Rules**: do not propose new doc systems/folders unless requested; ticket-linked analysis → docs/analysis/; temporary notes → docs/scratch/; recommend promotion of scratch to analysis/architecture when long-term, do not move automatically; structure changes only in dedicated sessions.

4. **docs/DEVELOPMENT_GUIDE.md**
   - References to `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md` updated to `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`.
   - Added **Ticket Workflow: Analysis vs Scratch**: formal root-cause/implementation-plan → docs/analysis/; temporary debug/experiments → docs/scratch/; documentation structure changes out of scope for normal ticket work.

5. **docs/architecture/**
   - **DIRECTORY_STRUCTURE.md**, **CURRENT_FILE_STRUCTURE.md**, **REFACTORING_SUMMARY.md**: added one-line notice at top: "This document is reference/supplementary material. For canonical rules, see docs/SSOT.md and docs/ARCHITECTURE.md."
   - **ROUTES_DIRECT_MONGO_ACCESS.md** (new): canonical list of routes/code with direct MongoDB access; content extracted from USECASE_REFACTOR_ROADMAP so references have a single target. Replaces previous references to docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md.

6. **docs/ARCHITECTURE.md**, **docs/USECASE_REFACTOR_ROADMAP.md**
   - All references to `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md` updated to `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`.

7. **docs/scratch/README.md** (new)
   - States scratch is temporary and non-canonical; important conclusions should be promoted to docs/analysis/ or docs/architecture/; do not rely on scratch for decisions.

8. **docs/tickets/README.md**
   - Added **Ticket vs Analysis vs Scratch**: ticket = task definition; analysis = formal ticket-linked (root cause, plan); scratch = temporary notes.
   - Ticket naming: clarified underscores, added example BUG-003_persona_not_rendered_in_new_chat_sessions.md.

9. **docs/tickets/OrderForm.md**
   - Added notice at top: "This is a helper prompt/order form, not a ticket file."

10. **docs/tickets/MS-01/**
    - **BUG-003** ticket renamed: `BUG-003 Persona Not Rendered in New Chat Sessions.md` → `BUG-003_persona_not_rendered_in_new_chat_sessions.md` (naming convention alignment). Old file removed; link in docs/analysis/BUG-003-persona-not-rendered-in-new-chat-analysis.md updated to new path.

---

## What was promoted

- **ROUTES_DIRECT_MONGO_ACCESS**: Previously referenced under docs/scratch/ (file was not present in workspace). Content is now in **docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md** as the single reference. All references in ARCHITECTURE, DEVELOPMENT_GUIDE, USECASE_REFACTOR_ROADMAP point to this file.

---

## What remains non-canonical

- **docs/scratch/** — Temporary; contents are not source of truth. No stub was added in scratch for ROUTES_DIRECT_MONGO_ACCESS because the file did not exist there; the canonical copy lives in docs/architecture/.
- **docs/architecture/** — Supporting/reference only; canonical structure and rules remain in docs/SSOT.md and docs/ARCHITECTURE.md.
- **docs/logs/**, **docs/misc/** — Unchanged; not declared canonical in this pass.

---

## Canonical reading order (from SSOT)

1. docs/SSOT.md  
2. docs/ARCHITECTURE.md  
3. docs/AI_AGENT_RULES.md  
4. docs/DEVELOPMENT_GUIDE.md  
5. docs/AI_ENTRYPOINT.md  
6. Assigned ticket under docs/tickets/  
7. Related formal analysis under docs/analysis/

---

## Manual review / follow-up

- **BUG-002**: No BUG-002 scratch documents were present in the workspace; no consolidated analysis file was created. If BUG-002_FINAL_SUMMARY or similar exist elsewhere, consider consolidating into docs/analysis/BUG-002_game_character_selection_not_applied_analysis.md and adding a "formal analysis is in docs/analysis/..." notice at the top of those scratch docs.
- **docs/README.md**: Still mentions docs/scratch/ and reading order; may be updated in a later pass to point to SSOT for canonical order and structure lock.
