# Ticket Title

Short description of the task.

Example:

BUG-001 Character CDN Domain Fix

---

# Metadata

Type: BUG | TASK | FEAT  
Severity: minor | major | critical  
Layer: api | domain | usecase | adapter | infra  
Milestone: MS-XX

---

# Problem

Describe the issue clearly.

Include:

- current behavior
- expected behavior
- impact

Example:

Current behavior:

Expected behavior:

Impact:

---

# Context

Provide technical context to help the AI locate the relevant code.

Include:

- relevant modules
- config values
- architecture hints

Example:

Relevant files:

apps/api/...  
src/usecases/...  
adapters/...  

Architecture rule:

API Route → Usecase → Adapter

---

# Scope

Define what this ticket is allowed to change.

Allowed:

- specific logic changes
- configuration updates

Not allowed:

- database schema changes
- infrastructure changes
- unrelated refactors
- large architecture modifications

---

# Strategy

Provide implementation hints.

Example approaches:

- update payload handling
- modify service logic
- adjust configuration

Example:

Ensure required parameters are passed through API → Usecase → Adapter.

---

# Acceptance Criteria

Define when the ticket is complete.

Example:

1 Expected behavior works correctly

2 API responses contain correct values

3 Existing functionality remains unchanged

---

# Verification

Manual verification steps.

Example:

1 Start API  
2 Trigger feature scenario  
3 Inspect response or network request  
4 Confirm expected behavior  

---

# Ticket Size Rule

Tickets should remain **small and focused**.

A single ticket should typically modify:

- 1–3 files
- a single logical change

Large refactors should be split into multiple tickets.

---

# AI Implementation Instructions

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

# Important Rule

One ticket should produce:

1 branch  
1 pull request

---

# Development Principles

Arcanaverse follows **AI-native development**.

Principles:

- SSOT
- Architecture-first development
- Ticket-driven development
- AI-assisted implementation