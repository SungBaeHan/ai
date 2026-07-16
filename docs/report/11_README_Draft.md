# Arcanaverse (TRPG AI)

> GitHub README 초안 — 코드 기준 (2026-06-14)

---

## Overview

**Arcanaverse**는 AI를 게임 마스터(GM)로 활용하는 웹 기반 TRPG 플랫폼입니다.  
세계관·캐릭터·게임을 생성하고, 턴 기반 플레이와 AI 채팅을 지원합니다.

개발 방식: **AI-assisted ticket-driven development** (`docs/tickets/`)

---

## Features

- Google OAuth 로그인
- 캐릭터 / 세계관 생성 (이미지 업로드 + AI 상세 생성)
- 게임 생성 (world + characters + rules)
- 턴 기반 TRPG (`JSON` 구조화 LLM 응답)
- 캐릭터·세계관 TRPG 채팅
- 페르소나 시스템
- My List / My Create
- Cloudflare R2 이미지 CDN

**Planned / 미구현:** Stripe 결제, Admin UI, RAG 채팅(현재 OFF)

---

## Tech Stack

| Layer | Tech |
|-------|------|
| API | Python 3.12, FastAPI, Uvicorn |
| DB | MongoDB |
| LLM | OpenAI (default) |
| Storage | Cloudflare R2 |
| Frontend | Static HTML (`apps/web-html/`) |
| Deploy | Docker, Nginx, Oracle VM, Cloudflare Pages |

---

## Architecture

```
Browser → Cloudflare Pages (static) + api.arcanaverse.ai (FastAPI)
                ↓
         MongoDB, OpenAI, R2, Qdrant
```

상세: [`docs/02_Architecture.md`](02_Architecture.md)

목표 패턴: **API Route → Usecase → Adapter** (레거시 route는 Mongo 직접 접근)

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- MongoDB URI
- OpenAI API Key
- (Optional) R2 credentials, Google OAuth Client ID

### Environment Variables

최소 설정:

```bash
MONGO_URI=mongodb+srv://...
OPENAI_API_KEY=sk-...
JWT_SECRET=<strong-secret>
PORT=8000
GOOGLE_CLIENT_ID=<google-client-id>   # 로그인 시
```

전체: [`docs/01_Project_Overview.md`](01_Project_Overview.md)

---

## Run Locally

```bash
docker network create app-net
cd infra
docker compose up -d --build
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

프론트: `apps/web-html/` 정적 서빙 → API `http://localhost:8000`

---

## Deployment

- **API:** Oracle VM + Docker + Nginx (`infra/`)
- **Frontend:** Cloudflare Pages (`arcanaverse.ai`)
- **CDN:** `https://img.arcanaverse.ai`
- **CI:** GitHub Actions `deploy-dev.yml` → SSH deploy

---

## Documentation Index

| 문서 | 설명 |
|------|------|
| [01_Project_Overview](01_Project_Overview.md) | 개요·실행·환경변수 |
| [02_Architecture](02_Architecture.md) | 시스템 아키텍처 |
| [03_Feature_Index](03_Feature_Index.md) | 기능 목록 |
| [04_API_Documentation](04_API_Documentation.md) | API |
| [05_Database_Schema](05_Database_Schema.md) | DB |
| [06_Folder_Structure](06_Folder_Structure.md) | 폴더 구조 |
| [07_AI_Workflow](07_AI_Workflow.md) | LLM 워크플로 |
| [08_Game_Flow](08_Game_Flow.md) | 게임 플로우 |
| [09_Tech_Debt](09_Tech_Debt.md) | 기술 부채 |
| [10_TODO_and_Roadmap](10_TODO_and_Roadmap.md) | TODO·로드맵 |
| [12_Development_Status_Report](12_Development_Status_Report.md) | 현황 리포트 |
| [13_TRPG_Engine](13_TRPG_Engine.md) | TRPG 엔진 |
| [14_Code_Trace_Map](14_Code_Trace_Map.md) | 코드 추적표 |
| [15_MVP_Scope](15_MVP_Scope.md) | MVP 범위 |

전체 인덱스: [`analysis/00_Documentation_Index.md`](analysis/00_Documentation_Index.md)

기존 SSOT: [`SSOT.md`](SSOT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Current Status

- **핵심 루프:** 게임 생성 → 턴 플레이 → AI 채팅 **동작** (코드 기준)
- **미구현:** Stripe, Admin, Rules 실행 엔진, RAG(비활성)
- **프로덕션 준비:** P0 보안·턴 안정성 해결 전 **제한적 데모** 권장
- **상세:** `12_Development_Status_Report.md`, `15_MVP_Scope.md`

---

## License

Demo and learning purposes. Commercial use requires permission. (See root `README.md`)

---

## 분석 기준 파일

- Root `README.md`, `apps/api/main.py`, `infra/docker-compose.yml`
