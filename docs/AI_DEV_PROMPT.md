# AI Development Prompt

This document defines the **standard execution prompt for AI agents**
(Cursor, Codex, or similar tools) working on the Arcanaverse repository.

---

# Step 1 — Read Core Documents

Before implementing any issue, read the following documents in order:

1. docs/AI_ENTRYPOINT.md
2. docs/SSOT.md
3. docs/ARCHITECTURE.md
4. docs/AI_AGENT_RULES.md
5. docs/DEVELOPMENT_GUIDE.md

These documents define:

- repository structure
- architecture rules
- AI behavior constraints
- development workflow

---

# Step 2 — Read the Assigned Ticket

All work must be based on a **Markdown ticket**.

Ticket location:

docs/tickets/

Example:

docs/tickets/MS-01/BUG-002_game_character_selection_not_applied.md

The ticket defines:

- problem
- scope
- strategy
- acceptance criteria
- verification steps

AI agents must **follow the ticket strictly**.

---

# Development Rules

1. Follow the ticket scope strictly  
2. Do not modify unrelated files  
3. Avoid refactoring unless explicitly requested  
4. Do not modify infrastructure or environment configuration  
5. Do not change database schema unless explicitly requested  

---

# Architecture Rule

API routes must **not access MongoDB directly**.

Use the architecture structure:

Route → Usecase → Adapter

Legacy code may still use direct Mongo access, but **new implementations must follow the architecture rule**.

---

# Implementation Workflow

Before coding, the AI must provide:

1. root cause analysis
2. files to modify
3. implementation plan

Wait for approval before implementing.

---

# Implementation Constraints

When implementing the ticket:

- make **minimal changes**
- avoid modifying unrelated modules
- preserve existing functionality

---

# Post-Implementation Report

After coding, the AI must provide:

- files changed
- summary of changes
- verification steps
- potential risks

---

## Report Rules (MANDATORY)

After implementation, the AI MUST:

1. Create an implementation report under `docs/analysis/`

2. The report must follow:

- `docs/analysis/README.md` (naming rules)
- `docs/QA_AND_DONE.md` (report structure)

3. The report MUST include:

- Ticket ID
- Summary of changes
- Files modified
- Root cause analysis
- Implementation details
- Verification steps
- Risks / limitations
- Completion Status section

4. Completion Status must be:

- Implementation Done: YES
- Release Verified: PENDING

5. Report filename format:

docs/analysis/[TICKET-ID]-report.md

Example:

docs/analysis/FEAT-MyList-001-report.md

---

# Pull Request Rule

One ticket should produce:

1 branch  
1 pull request  

---

# Execution Rules (IMPORTANT)

When executing a ticket, the AI must:

1. Read and follow the ticket exactly  
2. Do not skip analysis phase  
3. Do not start coding immediately  
4. Keep the change small and focused  
5. Do not introduce unrelated changes  

---

# Final Principle

Arcanaverse follows **AI-native development**.

Principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation
- Analysis-driven iteration