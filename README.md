# Arcanaverse

AI-Native TRPG Platform

Arcanaverse는 AI를 게임 마스터(GM)처럼 활용하여  
세계관 생성 → 캐릭터 생성 → 게임 생성 → 턴 기반 TRPG 플레이를  
웹에서 실행할 수 있는 AI-Native 게임 플랫폼입니다.

This project is developed using an **AI-assisted ticket-driven workflow**.

---

# Architecture

이 프로젝트는 다음 레이어 구조를 따릅니다.


apps/api API layer (FastAPI)
src/domain Domain entities
src/usecases Application logic
adapters External integrations
infra Deployment / Docker
docs Project documentation

Architecture rule:

API Route → Usecase → Adapter

API route에서 MongoDB 직접 접근은 **legacy 코드로 간주됩니다.**

자세한 구조는 아래 문서를 참고하세요.

docs/ARCHITECTURE.md

---

# Development Workflow (AI Ticket System)

Arcanaverse는 **AI-assisted ticket-driven development workflow**를 사용합니다.

모든 개발 작업은 **Markdown 티켓 기반으로 수행됩니다.**

Ticket → Cursor → Implementation → PR → Verification

---

# Ticket System

All development tasks must be defined as Markdown tickets under:

docs/tickets/

Example:

docs/tickets/MS-01/BUG-001_character_cdn.md

Workflow:

1. Create ticket
2. Cursor reads the ticket
3. Cursor proposes implementation plan
4. Implementation
5. Verification
6. Pull Request

---

# Core Development Documents

AI 에이전트는 작업 전에 다음 문서를 반드시 읽어야 합니다.

docs/SSOT.md
docs/ARCHITECTURE.md
docs/AI_AGENT_RULES.md
docs/DEVELOPMENT_GUIDE.md
docs/AI_DEV_PROMPT.md

각 문서 역할:

| Document | Purpose |
|--------|--------|
| SSOT.md | Repository single source of truth |
| ARCHITECTURE.md | System architecture |
| AI_AGENT_RULES.md | AI behavior rules |
| DEVELOPMENT_GUIDE.md | Development workflow |
| AI_DEV_PROMPT.md | Cursor execution prompt |

---

# External Integrations

현재 프로젝트는 다음 외부 시스템과 연동됩니다.

MongoDB
Cloudflare R2
OpenAI
Ollama
Stripe (planned)

---

# Asset Storage

이미지 및 에셋은 Cloudflare R2에 저장됩니다.

Public CDN domain:

https://img.arcanaverse.ai

Asset URL structure:

https://img.arcanaverse.ai/assets/{type}/{file}

Example:

https://img.arcanaverse.ai/assets/char/123.png

---

# Documentation

프로젝트 문서는 `docs/` 디렉토리에 있습니다.

docs/
README.md
SSOT.md
ARCHITECTURE.md
AI_AGENT_RULES.md
DEVELOPMENT_GUIDE.md
AI_DEV_PROMPT.md
USECASE_REFACTOR_ROADMAP.md
tickets/
scratch/

Documentation index:

docs/README.md

---

# Development Philosophy

Arcanaverse는 **AI-native solo development 방식**으로 개발됩니다.

Principles:

SSOT
Architecture-first
Ticket-driven development
AI-assisted implementation

---

# License

TBD