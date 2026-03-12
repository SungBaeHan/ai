# AI Agent Development Rules

This document defines how AI agents (Cursor, Codex, GPT, etc.) must operate when modifying this repository.

The goal is to ensure safe, predictable, and minimal-impact development when AI agents implement GitHub issues.

---

# 1. Source of Truth

AI agents MUST read and follow the following documents before implementing any change.

1. docs/SSOT.md
2. docs/PRD/*
3. GitHub Issue description

If there is any conflict between documents:

SSOT.md takes priority.

---

# 2. Development Scope

AI agents must follow the issue scope strictly.

Allowed:

- Fix the specific bug described in the issue
- Implement the requested feature
- Modify files directly related to the issue

NOT allowed:

- Refactor unrelated code
- Rename directories
- Modify architecture
- Change infrastructure configuration
- Modify environment configuration
- Modify database schema unless explicitly requested

If the issue requires architectural changes,
the agent must stop and ask for clarification.

---

# 3. Issue-driven Development

All development must be based on a GitHub Issue.

Rules:

1 Issue = 1 Branch = 1 Pull Request

Agents must never combine multiple issues into one implementation.

---

# 4. Implementation Workflow

Before writing any code, the agent must:

1. Read the issue
2. Search the repository for related code
3. Identify affected modules
4. Provide a short implementation plan

Example:

Implementation Plan:

- locate image URL generation
- replace R2 public URL with CDN base
- update serializer logic
- verify API response

Only after the plan is confirmed should the agent proceed with code changes.

---

# 5. Code Modification Rules

Agents should follow these rules when editing code.

Preferred actions:

- minimal code change
- reuse existing patterns
- follow existing architecture
- keep functions small and clear

Avoid:

- large refactoring
- rewriting working modules
- changing folder structures
- modifying unrelated files

---

# 6. Architecture Layers

This project follows a layered architecture.

apps/api
API layer

src/domain
domain logic

src/usecases
application use cases

adapters
external integrations (DB, storage, LLM, Stripe)

infra
deployment and infrastructure

Agents should respect these boundaries.

Example:

Business logic must NOT be implemented in API routes.

Direct MongoDB access from API routes is considered legacy.

New code must follow this structure:

API Route → Usecase → Adapter

Existing direct MongoDB access is allowed only for legacy code and should not be used for new features.

---

# 7. External Integration Rules

External services include:

- MongoDB
- R2 Storage
- Cloudflare
- OpenAI
- Stripe

Rules:

Agents must NOT:

- modify credentials
- modify API keys
- change connection logic
- change environment variables

unless explicitly required by the issue.

---

# 8. Database Rules

Database schema changes are NOT allowed unless explicitly specified.

Allowed:

- read queries
- safe query adjustments

NOT allowed:

- schema changes
- migration scripts
- collection renaming

---

# 9. API Stability

Existing API responses must remain backward compatible.

Agents must NOT:

- remove response fields
- rename response fields
- change response structure

unless the issue explicitly requires it.

---

# 10. Logging and Error Handling

When modifying code:

- preserve existing logging
- do not remove error handling
- avoid silent failures

---

# 11. Testing

If the repository contains tests:

Agents should update or add tests when possible.

Minimum expectations:

- API still runs
- main flows not broken

---

# 12. Output Format

After completing implementation, the agent must provide a summary.

Required output format:

### Implementation Summary

Files Modified:

- file/path/example.py
- file/path/another.py

Key Changes:

- replaced R2 public URL with CDN base
- updated serializer logic

Verification Steps:

1. run API
2. open character list
3. verify image URL domain

Remaining Risks:

- potential legacy data containing old URLs

---

# 13. Safety Rule

If the agent is uncertain about:

- architecture changes
- database changes
- infrastructure changes

The agent must STOP and request clarification.

Do not guess.

---

# 14. Preferred Development Style

Agents should prefer:

- small commits
- incremental changes
- readable code

Avoid:

- large rewrites
- speculative refactoring

---

# 15. Repository Stability

The primary goal is to keep the system stable.

Bug fixes and small improvements are preferred over risky refactoring.

---

End of Rules