# AI Development Prompt

Before implementing any issue, read the following:

- docs/SSOT.md
- docs/ARCHITECTURE.md
- docs/AI_AGENT_RULES.md
- docs/DEVELOPMENT_GUIDE.md

Development rules:

1. Follow the GitHub issue scope strictly
2. Do not modify unrelated files
3. Avoid refactoring unless explicitly requested
4. Do not modify infrastructure or environment configuration
5. Do not change database schema unless requested

Architecture rule:

API routes must not access MongoDB directly.

Use the structure:

Route → Usecase → Adapter

Legacy code may still use direct Mongo access but new code must not.

Implementation workflow:

1. Read the issue
2. Identify affected modules
3. Provide a short implementation plan
4. Implement minimal changes
5. Provide verification steps
