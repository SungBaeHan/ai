# TRPG 레포 문서/운영체계 구조 인벤토리

작성일: 2026-03-24  
대상 레포: `F:/git/ai`

이 문서는 단순 트리 나열이 아니라, **티켓 기반 개발 운영에 실제로 쓰이는 문서/템플릿/가이드**를 식별하고  
AI 오케스트레이터 레포로의 복제 후보를 선별하기 위한 인벤토리다.

---

## 1) 레포 상위 구조(운영 관점 요약)

코드/설정 파일 기준으로 확인된 상위 디렉터리:

- `.github/` (이슈 템플릿, 배포 워크플로)
- `apps/` (API, 웹 HTML, LLM 프롬프트 등 실행 코드)
- `src/`, `adapters/` (클린 아키텍처 계층)
- `docs/` (운영 문서 허브: 티켓/분석/아키텍처/로그/인프라)
- `infra/`, `docker/` (운영/배포 구성)
- `scripts/`, `tests/`, `data/`, `html/`, `packages/`

문서 운영 체계의 중심은 `docs/`이며, 특히 `docs/SSOT.md`, `docs/tickets/`, `docs/analysis/`, `docs/QA_AND_DONE.md`가 핵심 축이다.

---

## 2) 우선 식별 결과 (요청 범주 기준)

- **루트 문서**: `README.md` 확인
- **docs/ 하위 문서**: 핵심 운영 문서군 확인 (`SSOT`, `ARCHITECTURE`, `AI_*`, `QA_AND_DONE` 등)
- **docs/tickets/**: `README`, `_TEMPLATE`, `OrderForm`, 실제 티켓 파일들 확인
- **docs/templates/**: 현재 **디렉터리/파일 없음**
- **docs/analysis/**: `README` + 티켓별 리포트/분석 문서들 확인
- **QA / Done / Prompt / Rules / SSOT / Architecture 관련**: 문서군 전수 확인 (아래 표)

---

## 3) 개발 운영 표준 파일 인벤토리 (복제 우선 검토 대상)

| 경로 | 파일명 | 역할 설명 | 티켓 기반 개발 운영 파일 | AI 오케스트레이터 복제 후보(초안) |
|---|---|---|---|---|
| `/` | `README.md` | 레포 개요 + 아키텍처 규칙 + 티켓 기반 워크플로의 최상위 소개 문서. 필독 문서 목록과 원칙을 제시. | 예 | 수정 후 복제 |
| `docs/` | `README.md` | docs 허브 인덱스. 코어 문서 읽기 순서/워크플로를 안내. | 예 | 수정 후 복제 |
| `docs/` | `SSOT.md` | 저장소 단일 진실 소스. 구조 책임, 변경 규칙, 문서 체계 락, AI 읽기 순서를 정의. | 예 | 그대로 복제 가능 |
| `docs/` | `ARCHITECTURE.md` | 계층/엔트리포인트/외부 연동/레거시 이슈를 정리한 아키텍처 기준 문서. | 예 | 수정 후 복제 |
| `docs/` | `AI_ENTRYPOINT.md` | AI 작업 시작 절차와 필수 읽기 순서를 정의하는 엔트리 문서. | 예 | 그대로 복제 가능 |
| `docs/` | `AI_AGENT_RULES.md` | AI 에이전트 행동 규칙(범위 통제, 안전 규칙, 문서 규칙 등) 정의. | 예 | 그대로 복제 가능 |
| `docs/` | `DEVELOPMENT_GUIDE.md` | 이슈/티켓 기반 구현 절차, 레이어 규칙, 검증 출력 포맷을 안내. | 예 | 그대로 복제 가능 |
| `docs/` | `AI_DEV_PROMPT.md` | AI 실행용 표준 프롬프트. 작업 전/후 출력 형식과 리포트 작성 의무를 명시. | 예 | 그대로 복제 가능 |
| `docs/` | `QA_AND_DONE.md` | DoD, QA 체크리스트, 리포트 위치/구조/완료 판정 기준 정의. | 예 | 그대로 복제 가능 |
| `docs/` | `GPT_COLLABORATION_RULES.md` | GPT의 역할 경계(티켓 생성/분석/아키텍처 모드)와 템플릿 고정 규칙 정의. | 예 | 그대로 복제 가능 |
| `docs/` | `GPT_TICKET_MODE_RULE.md` | 티켓 생성 시 엄수할 출력/범위 규칙을 간결히 강제하는 보조 규칙 문서. | 예 | 그대로 복제 가능 |
| `docs/tickets/` | `README.md` | 티켓 워크플로/네이밍/구조/Ticket vs Analysis vs Scratch 구분 규칙 제공. | 예 | 그대로 복제 가능 |
| `docs/tickets/` | `_TEMPLATE.md` | 티켓 표준 템플릿(Problem/Scope/Strategy/AC/Verification 등) 원본. | 예 | 그대로 복제 가능 |
| `docs/tickets/` | `OrderForm.md` | AI에게 특정 티켓 경로를 실행 지시할 때 쓰는 헬퍼 폼(티켓 본문은 아님). | 예 | 수정 후 복제 |
| `docs/analysis/` | `README.md` | 분석/구현 리포트 저장 규칙, 네이밍, 티켓-리포트 1:1 매핑 원칙 정의. | 예 | 그대로 복제 가능 |
| `docs/` | `DOCS_STRUCTURE_CHANGELOG.md` | 문서 체계 정리 이력 및 canonical/non-canonical 경계 변경 기록. | 예 | 수정 후 복제 |
| `docs/` | `DOCS_STRUCTURE_RESULT.md` | 문서 구조 정리 결과 보고서(무엇을 바꿨는지, 무엇을 남겼는지) 정리. | 예 | 수정 후 복제 |
| `docs/` | `USECASE_REFACTOR_ROADMAP.md` | 레거시 접근을 표준 아키텍처로 이관하기 위한 리팩터 로드맵. | 부분(보조) | 수정 후 복제 |
| `docs/architecture/` | `ROUTES_DIRECT_MONGO_ACCESS.md` | 표준 패턴 위반 지점을 추적하는 refactor 기준 목록 문서. | 부분(보조) | 수정 후 복제 |
| `docs/architecture/` | `DIRECTORY_STRUCTURE.md` | 디렉터리 스냅샷 참조 문서(상단에 supplementary 성격 명시). | 부분(보조) | 수정 후 복제 |
| `docs/architecture/` | `CURRENT_FILE_STRUCTURE.md` | 현행 파일 구조 참조 스냅샷. canonical은 아님. | 부분(보조) | 수정 후 복제 |
| `docs/architecture/` | `REFACTORING_SUMMARY.md` | 과거 리팩터링 히스토리/요약(참고용). | 아니오 | 복제 불필요 |
| `.github/ISSUE_TEMPLATE/` | `bug.yml` | Bug 이슈 입력 템플릿. 심각도/레이어/재현/기술 컨텍스트 수집에 유효. | 예(입력원) | 그대로 복제 가능 |
| `.github/ISSUE_TEMPLATE/` | `feature.yml` | Feature 이슈 입력 템플릿. 요구사항/비범위/아키텍처 영향 수집. | 예(입력원) | 그대로 복제 가능 |
| `.github/ISSUE_TEMPLATE/` | `task.yml` | Task 이슈 입력 템플릿. Scope Lock, 전략, 기술 컨텍스트 정형화. | 예(입력원) | 그대로 복제 가능 |
| `.github/ISSUE_TEMPLATE/` | `config.yml` | 이슈 작성 정책(빈 이슈 비활성화, 문의 링크) 설정. | 부분 | 그대로 복제 가능 |
| `.github/workflows/` | `deploy-dev.yml` | dev 브랜치 push 시 Oracle VM 원격 배포 수행하는 CI 워크플로. | 아니오(배포체계) | 수정 후 복제 |
| `infra/` | `README-OPERATIONS.md` | Cloudflare-VM-Nginx 운영 기준, 배포/점검/장애 대응 절차 정리. | 아니오(운영 Runbook) | 수정 후 복제 |
| `infra/` | `README-reverse-proxy.md` | 리버스 프록시 설치/검증/트러블슈팅 절차 문서. | 아니오(운영 Runbook) | 수정 후 복제 |

---

## 4) TRPG 도메인 전용/사례 중심 파일 인벤토리

아래는 티켓 시스템 자체는 맞지만, 내용이 **TRPG UI/페르소나/MyList 시나리오에 강하게 종속**되어  
AI 오케스트레이터 레포로는 보통 직접 복제 대상이 아니다.

| 경로 | 파일명 | 역할 설명 | 티켓 기반 개발 운영 파일 | AI 오케스트레이터 복제 후보(초안) |
|---|---|---|---|---|
| `docs/tickets/MS-01/` | `BUG-001_character_cdn.md` | TRPG 캐릭터 CDN URL 문제를 정의한 버그 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-002_game_character_selection_not_applied.md` | 게임 생성 시 캐릭터 선택 미반영 이슈 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-003_persona_not_rendered_in_new_chat_sessions.md` | 신규 세션 페르소나 렌더링 불일치 이슈 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-004_persona_modal_not_closing_on_new_session_character_world.md` | 신규 세션 페르소나 모달 닫힘 문제 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `UX-001 Persona Toast Message Unification.md` | 페르소나 토스트 문구 통일 UX 작업 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-03/` | `FEAT-MyList-001-my-list-navigation-structure.md` | My List UI 구조 정의 기능 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-MyList-002-my-list-scope-and-empty-state-fix.md` | My List 범위/Empty state 수정 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-MyList-003-my-list-navigation-routing-fix.md` | My List 메뉴 라우팅 수정 티켓. | 예 | 복제 불필요 |
| `docs/tickets/MS-01/` | `BUG-MyList-004-my-create-placeholder-state-fix.md` | My Create placeholder 동작 통일 티켓. | 예 | 복제 불필요 |
| `docs/analysis/` | `BUG-003-persona-not-rendered-in-new-chat-analysis.md` | BUG-003의 루트 원인과 구현 계획 분석서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `BUG-003-verification-report.md` | BUG-003 검증 결과 리포트. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `BUG-004-persona-modal-not-closing-report.md` | BUG-004 처리 결과 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `UX-001-persona-toast-message-unification-report.md` | UX-001 처리 결과 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `FEAT-MyList-001_report.md` | FEAT-MyList-001 구현 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `BUG-MyList-002_report.md` | BUG-MyList-002 구현 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `BUG-MyList-003_report.md` | BUG-MyList-003 구현 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `BUG-MyList-004_report.md` | BUG-MyList-004 구현 보고서. | 예(티켓 연결) | 복제 불필요 |
| `docs/analysis/` | `repo_structure_analysis.md` | 레포 구조 분석 보고서(문서 체계 개선 제안 포함). | 부분(운영 분석) | 수정 후 복제 |
| `docs/` | `QUICK_START.md` | Docker/Ollama 기반 TRPG 실행 빠른 시작 가이드. | 아니오 | 수정 후 복제 |
| `docs/` | `DOCS_STRUCTURE_CHANGELOG.md` | 문서 구조 정리 변경 이력(해당 프로젝트 히스토리). | 부분 | 수정 후 복제 |
| `docs/` | `DOCS_STRUCTURE_RESULT.md` | 문서 구조 정리 결과 보고서(해당 프로젝트 맥락). | 부분 | 수정 후 복제 |
| `docs/infra/` | `GOOGLE_LOGIN_SETUP.md` | TRPG 웹 로그인(구글 OAuth) 설정 가이드. | 아니오 | 복제 불필요 |
| `docs/misc/` | `UNUSED_FEATURES.md` | 현재 미사용 기능 목록(프로덕트 특화). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-01-27.md` | 날짜별 작업 로그(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-05.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-07.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-19.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-21.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-24.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-11-25.md` | 날짜별 배포 이력(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-12-03.md` | 날짜별 작업 로그(프로젝트 이력). | 아니오 | 복제 불필요 |
| `docs/logs/` | `2025-12-04.md` | 날짜별 작업 로그(프로젝트 이력). | 아니오 | 복제 불필요 |

---

## 5) docs/templates/ 상태

- `docs/templates/` 디렉터리는 현재 레포에 존재하지 않음.
- 템플릿 역할은 현재 `docs/tickets/_TEMPLATE.md` 및 `.github/ISSUE_TEMPLATE/*.yml`로 분산 운영 중.

---

## 6) 복제 후보 요약

### A. 그대로 복제 가능

- `docs/SSOT.md`
- `docs/AI_ENTRYPOINT.md`
- `docs/AI_AGENT_RULES.md`
- `docs/DEVELOPMENT_GUIDE.md`
- `docs/AI_DEV_PROMPT.md`
- `docs/QA_AND_DONE.md`
- `docs/tickets/README.md`
- `docs/tickets/_TEMPLATE.md`
- `docs/analysis/README.md`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/feature.yml`
- `.github/ISSUE_TEMPLATE/task.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `docs/GPT_COLLABORATION_RULES.md`
- `docs/GPT_TICKET_MODE_RULE.md`

### B. 내용 수정 후 복제

- `README.md`, `docs/README.md` (도메인/서비스명 교체 필요)
- `docs/ARCHITECTURE.md` (TRPG/게임 도메인 기술을 오케스트레이터 구조로 치환)
- `docs/USECASE_REFACTOR_ROADMAP.md`, `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md` (현재 코드베이스 기준으로 재작성)
- `docs/architecture/DIRECTORY_STRUCTURE.md`, `docs/architecture/CURRENT_FILE_STRUCTURE.md` (대상 레포 구조로 재스냅샷 필요)
- `.github/workflows/deploy-dev.yml` (배포 대상/서버/브랜치 정책 맞춤화)
- `infra/README-OPERATIONS.md`, `infra/README-reverse-proxy.md` (인프라 토폴로지에 맞춰 재작성)
- `docs/QUICK_START.md` (런타임/서비스 구성 차이 반영)
- `docs/analysis/repo_structure_analysis.md`, `docs/DOCS_STRUCTURE_CHANGELOG.md`, `docs/DOCS_STRUCTURE_RESULT.md` (초기 세팅 시 1회 재생성용)
- `docs/tickets/OrderForm.md` (티켓 경로/지시 포맷만 맞춤 변경)

### C. 복제 불필요

- `docs/tickets/MS-*/`의 개별 티켓 본문들 (TRPG 문제 정의 자체)
- `docs/analysis/`의 티켓별 결과 보고서들
- `docs/logs/*.md` (프로젝트 이력)
- `docs/infra/GOOGLE_LOGIN_SETUP.md`
- `docs/misc/UNUSED_FEATURES.md`

---

## 7) 결론

이 레포의 티켓 기반 운영 체계는 **문서 중심 표준 세트가 이미 잘 분리**되어 있으며,  
AI 오케스트레이터 레포로 이식할 때는 **표준 규칙 문서 + 템플릿 문서 + 이슈 템플릿**을 우선 그대로 복제하고,  
아키텍처/인프라/도메인 사례 문서는 대상 레포 맥락에 맞춰 수정 복제하는 방식이 가장 안정적이다.
