# Arcanaverse Documentation

이 디렉토리는 **Arcanaverse 프로젝트의 개발 문서와 아키텍처 문서**를 포함합니다.

Arcanaverse는 **AI-assisted, ticket-driven development workflow**를 기반으로 개발됩니다.

모든 개발 작업은 **Markdown 티켓을 기준으로 진행됩니다.**

---

# Architecture Overview

프로젝트는 다음 레이어 구조를 따릅니다.


apps/api API layer
src/domain Domain models
src/usecases Application logic
adapters External integrations
infra Deployment / Docker
docs Documentation


Architecture rule:


API Route → Usecase → Adapter


Direct MongoDB access from API routes is considered **legacy** and should be gradually removed.

---

# Core Development Documents

AI 에이전트는 작업 전에 다음 문서를 반드시 읽어야 합니다.

Recommended reading order:

1. SSOT.md
2. ARCHITECTURE.md
3. AI_AGENT_RULES.md
4. DEVELOPMENT_GUIDE.md
5. AI_DEV_PROMPT.md

각 문서 역할:

| Document | Purpose |
|--------|--------|
| SSOT.md | Repository structure 기준 |
| ARCHITECTURE.md | 시스템 아키텍처 |
| AI_AGENT_RULES.md | AI 행동 규칙 |
| DEVELOPMENT_GUIDE.md | 개발 절차 |
| AI_DEV_PROMPT.md | Cursor 실행 프롬프트 |

---

# AI Development Workflow

Arcanaverse는 **Ticket-Driven Development** 방식을 사용합니다.

Development flow:


Ticket
↓
Cursor / Codex
↓
Implementation
↓
Pull Request
↓
Verification


AI는 **반드시 티켓을 기준으로 작업해야 합니다.**

---

# Ticket System

모든 개발 작업은 **Markdown 티켓**으로 정의됩니다.

Ticket location:


docs/tickets/


Example:


docs/tickets/MS-01/BUG-001_character_cdn.md


티켓 작성 규칙은 다음 문서를 참고하세요.


docs/tickets/README.md


---

# Refactoring Roadmap

기존 일부 API route는 MongoDB에 직접 접근합니다.

이는 legacy 구조이며 점진적으로 다음 구조로 이동합니다.


Route → Usecase → Adapter


Roadmap document:


USECASE_REFACTOR_ROADMAP.md


---

# External Integrations

현재 사용 중인 외부 시스템:

- MongoDB
- Cloudflare R2
- OpenAI
- Ollama
- Stripe (planned)

---

# Scratch Documents

분석 및 임시 문서는 다음 디렉토리에 위치합니다.


docs/scratch/


Example:


ARCHITECTURE_OVERVIEW.md
ROUTES_DIRECT_MONGO_ACCESS.md
SEARCH_R2_DEV_DOMAIN.md
VERIFICATION_ASSET_URL_PREFIX.md


---

# Documentation Structure


docs/

README.md
AI_ENTRYPOINT.md

SSOT.md
ARCHITECTURE.md
AI_AGENT_RULES.md
DEVELOPMENT_GUIDE.md
AI_DEV_PROMPT.md
USECASE_REFACTOR_ROADMAP.md

tickets/
scratch/