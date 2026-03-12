# AI Entry Point

This file defines the **starting instructions for AI agents** working on the Arcanaverse repository.

If you are an AI agent (Cursor, Codex, or similar), **read this document first**.

---

# Step 1 — Understand the Repository

Before performing any task, read the following documents **in order**:

1. docs/SSOT.md
2. docs/ARCHITECTURE.md
3. docs/AI_AGENT_RULES.md
4. docs/DEVELOPMENT_GUIDE.md

These documents define:

- repository structure
- architecture rules
- AI behavior rules
- development workflow

---

# Step 2 — Read the Assigned Ticket

All development work is defined using **Markdown tickets**.

Ticket location:


docs/tickets/


Example:


docs/tickets/MS-01/BUG-001_character_cdn.md


The ticket defines:

- problem
- scope
- strategy
- acceptance criteria
- verification steps

AI agents **must follow the ticket strictly**.

---

# Step 3 — Respect the Architecture

Arcanaverse follows the architecture rule:


API Route → Usecase → Adapter


API routes **must not access MongoDB directly** unless explicitly allowed.

Legacy code may still exist, but **new implementations must follow the architecture rule**.

---

# Step 4 — Respect the Ticket Scope

AI agents must **never modify files outside the scope defined in the ticket**.

Allowed:

- files listed in ticket context
- minimal required modifications

Not allowed:

- unrelated refactors
- architecture redesign
- infrastructure changes
- database schema changes

---

# Step 5 — Development Workflow

All development follows this process:


Ticket
↓
AI Implementation
↓
Pull Request
↓
Verification


One ticket should produce:


1 branch
1 pull request


---

# Step 6 — Implementation Process

Before coding the AI must provide:

- root cause analysis
- files to modify
- implementation plan

After coding the AI must provide:

- files changed
- summary of changes
- verification steps
- potential risks

---

# Important Principles

Arcanaverse follows **AI-native development**.

Core principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation

---

# Final Rule

If the ticket conflicts with architecture rules:


Architecture rules take priority.


When unsure:

- read SSOT
- read ARCHITECTURE
- then proceed.