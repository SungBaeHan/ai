# docs 디렉토리 구조 분석 리포트 (AI 개발 시스템 관점)

작성일: 2026-04-06

본 문서는 현재 `docs/` 실제 파일 구조를 기준으로, AI 개발 시스템에서 의미 있는 정보 흐름(규칙 -> 입력 -> 실행 -> 검증 -> 기록) 관점으로 재정리한 분석 리포트다.

---

## 1) 디렉토리 트리

```text
docs/
├─ README.md
├─ QUICK_START.md
├─ SSOT.md
├─ ARCHITECTURE.md
├─ AI_ENTRYPOINT.md
├─ AI_AGENT_RULES.md
├─ AI_DEV_PROMPT.md
├─ DEVELOPMENT_GUIDE.md
├─ USECASE_REFACTOR_ROADMAP.md
├─ QA_AND_DONE.md
├─ GPT_TICKET_MODE_RULE.md
├─ GPT_COLLABORATION_RULES.md
├─ DOCS_STRUCTURE_RESULT.md
├─ DOCS_STRUCTURE_CHANGELOG.md
├─ architecture/
│  ├─ CURRENT_FILE_STRUCTURE.md
│  ├─ DIRECTORY_STRUCTURE.md
│  ├─ REFACTORING_SUMMARY.md
│  └─ ROUTES_DIRECT_MONGO_ACCESS.md
├─ analysis/
│  ├─ README.md
│  ├─ repo_structure_analysis.md
│  ├─ trpg_repo_structure_inventory.md
│  ├─ FEAT-MyList-001_report.md
│  ├─ BUG-MyList-002_report.md
│  ├─ BUG-MyList-003_report.md
│  ├─ BUG-MyList-004_report.md
│  ├─ UX-001-persona-toast-message-unification-report.md
│  ├─ BUG-004-persona-modal-not-closing-report.md
│  ├─ BUG-003-persona-not-rendered-in-new-chat-analysis.md
│  └─ BUG-003-verification-report.md
├─ infra/
│  └─ GOOGLE_LOGIN_SETUP.md
├─ logs/
│  ├─ 2025-01-27.md
│  ├─ 2025-11-05.md
│  ├─ 2025-11-07.md
│  ├─ 2025-11-19.md
│  ├─ 2025-11-21.md
│  ├─ 2025-11-24.md
│  ├─ 2025-11-25.md
│  ├─ 2025-12-03.md
│  └─ 2025-12-04.md
├─ misc/
│  └─ UNUSED_FEATURES.md
├─ scratch/
│  ├─ README.md
│  ├─ ARCHITECTURE_OVERVIEW.md
│  ├─ BUG-002_FINAL_SUMMARY.md
│  ├─ BUG-002_FRONTEND_COMMIT_RENDER_PATH.md
│  ├─ DIAGNOSIS_REPORT.md
│  ├─ LOG_PATH_MAP.md
│  ├─ MongoSample.md
│  ├─ ROUTES_DIRECT_MONGO_ACCESS.md
│  ├─ SEARCH_R2_DEV_DOMAIN.md
│  ├─ SOLUTION_MAP.md
│  ├─ SOLUTION_STRUCTURE.md
│  ├─ Sample.md
│  ├─ VERIFICATION_ASSET_URL_PREFIX.md
│  ├─ bugfix_modal_infinite_append.md
│  ├─ current_repo_structure.md
│  ├─ game_chat_badge_render_audit.md
│  ├─ modal_infinite_debug_context.md
│  ├─ qa_done_structure_review.md
│  ├─ ux_infinite_skeleton.md
│  ├─ ux_infinite_skeleton_home_character_applied.md
│  ├─ ux_infinite_skeleton_search_and_create_game.md
│  ├─ ux_infinite_skeleton_search_and_create_game_applied.md
│  └─ world_chat_tree.md
└─ tickets/
   ├─ README.md
   ├─ _TEMPLATE.md
   ├─ OrderForm.md
   ├─ MS-01/
   │  ├─ BUG-001_character_cdn.md
   │  ├─ BUG-002_game_character_selection_not_applied.md
   │  ├─ BUG-003_persona_not_rendered_in_new_chat_sessions.md
   │  ├─ BUG-004_persona_modal_not_closing_on_new_session_character_world.md
   │  ├─ BUG-MyList-002-my-list-scope-and-empty-state-fix.md
   │  ├─ BUG-MyList-003-my-list-navigation-routing-fix.md
   │  ├─ BUG-MyList-004-my-create-placeholder-state-fix.md
   │  └─ UX-001 Persona Toast Message Unification.md
   └─ MS-03/
      └─ FEAT-MyList-001-my-list-navigation-structure.md
```

---

## 2) 각 파일의 역할 요약

아래는 AI 개발 운영 관점에서 파일 역할을 1줄로 요약한 목록이다.

### 2.1 루트 문서

- `docs/README.md`: docs 허브 소개, 기본 읽기 안내, 티켓 기반 개발 개요
- `docs/QUICK_START.md`: 로컬 실행/장애 대응용 빠른 운영 가이드
- `docs/SSOT.md`: 저장소/문서 체계의 최상위 기준(충돌 시 우선)
- `docs/ARCHITECTURE.md`: 시스템 계층/경계/API->Usecase->Adapter 규칙
- `docs/AI_ENTRYPOINT.md`: AI가 작업 시작 시 따를 정식 읽기 순서
- `docs/AI_AGENT_RULES.md`: AI 변경 범위/안전/금지사항 규정
- `docs/AI_DEV_PROMPT.md`: AI 실행 프롬프트 템플릿 및 리포트 의무
- `docs/DEVELOPMENT_GUIDE.md`: 이슈-브랜치-PR 중심 구현 절차 가이드
- `docs/USECASE_REFACTOR_ROADMAP.md`: 레거시 직접 DB 접근의 리팩터 우선순위/전략
- `docs/QA_AND_DONE.md`: Done 기준, QA 체크리스트, 보고서 필수 항목
- `docs/GPT_TICKET_MODE_RULE.md`: GPT 티켓 처리 시 동작 원칙(운영 규칙군)
- `docs/GPT_COLLABORATION_RULES.md`: GPT 협업 시 역할/커뮤니케이션 규칙
- `docs/DOCS_STRUCTURE_RESULT.md`: 과거 docs 구조 정리 결과 보고서
- `docs/DOCS_STRUCTURE_CHANGELOG.md`: docs 구조/규칙 변경 이력 요약

### 2.2 architecture/

- `docs/architecture/CURRENT_FILE_STRUCTURE.md`: 구조 스냅샷(참고용)
- `docs/architecture/DIRECTORY_STRUCTURE.md`: 디렉토리 구조 레퍼런스(참고용)
- `docs/architecture/REFACTORING_SUMMARY.md`: 리팩터링 이력/요약(히스토리)
- `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`: 라우트 직접 Mongo 접근 위치 목록(리팩터 기준표)

### 2.3 analysis/

- `docs/analysis/README.md`: 분석/구현 보고서 저장 규칙과 네이밍 규칙
- `docs/analysis/repo_structure_analysis.md`: 저장소 구조 분석 산출물
- `docs/analysis/trpg_repo_structure_inventory.md`: TRPG 레포 인벤토리 성격의 구조 기록
- `docs/analysis/FEAT-MyList-001_report.md`: FEAT-MyList-001 구현 결과 보고
- `docs/analysis/BUG-MyList-002_report.md`: BUG-MyList-002 구현 결과 보고
- `docs/analysis/BUG-MyList-003_report.md`: BUG-MyList-003 구현 결과 보고
- `docs/analysis/BUG-MyList-004_report.md`: BUG-MyList-004 구현 결과 보고
- `docs/analysis/UX-001-persona-toast-message-unification-report.md`: UX-001 결과 보고
- `docs/analysis/BUG-004-persona-modal-not-closing-report.md`: BUG-004 결과 보고
- `docs/analysis/BUG-003-persona-not-rendered-in-new-chat-analysis.md`: BUG-003 사전 분석 문서
- `docs/analysis/BUG-003-verification-report.md`: BUG-003 검증 중심 결과 문서

### 2.4 infra/

- `docs/infra/GOOGLE_LOGIN_SETUP.md`: 외부 인증 연동(구글 로그인) 설정 안내

### 2.5 logs/

- `docs/logs/2025-01-27.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-05.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-07.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-19.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-21.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-24.md`: 일자별 작업/운영 로그
- `docs/logs/2025-11-25.md`: 일자별 작업/운영 로그
- `docs/logs/2025-12-03.md`: 일자별 작업/운영 로그
- `docs/logs/2025-12-04.md`: 일자별 작업/운영 로그

### 2.6 misc/

- `docs/misc/UNUSED_FEATURES.md`: 비활성/미사용 기능 목록 및 정리 후보

### 2.7 scratch/

- `docs/scratch/README.md`: 임시 문서 목적/비준거성 안내
- `docs/scratch/ARCHITECTURE_OVERVIEW.md`: 임시 아키텍처 개요 정리
- `docs/scratch/BUG-002_FINAL_SUMMARY.md`: BUG-002 임시 최종 정리
- `docs/scratch/BUG-002_FRONTEND_COMMIT_RENDER_PATH.md`: BUG-002 프론트 경로 추적 메모
- `docs/scratch/DIAGNOSIS_REPORT.md`: 디버깅 진단 메모
- `docs/scratch/LOG_PATH_MAP.md`: 로그 경로 탐색 메모
- `docs/scratch/MongoSample.md`: Mongo 샘플/실험 기록
- `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md`: 직접 DB 접근 임시 메모(공식 기준은 architecture 하위 문서)
- `docs/scratch/SEARCH_R2_DEV_DOMAIN.md`: R2 도메인 검색/추적 메모
- `docs/scratch/SOLUTION_MAP.md`: 해결안 맵핑 초안
- `docs/scratch/SOLUTION_STRUCTURE.md`: 해결 구조 초안
- `docs/scratch/Sample.md`: 샘플 테스트 문서
- `docs/scratch/VERIFICATION_ASSET_URL_PREFIX.md`: 에셋 URL 검증 메모
- `docs/scratch/bugfix_modal_infinite_append.md`: 모달 무한 append 디버깅 메모
- `docs/scratch/current_repo_structure.md`: 저장소 구조 임시 스냅샷
- `docs/scratch/game_chat_badge_render_audit.md`: 게임 채팅 렌더 점검 메모
- `docs/scratch/modal_infinite_debug_context.md`: 모달 무한 이슈 컨텍스트
- `docs/scratch/qa_done_structure_review.md`: QA/Done 구조 검토 초안
- `docs/scratch/ux_infinite_skeleton.md`: UX 스켈레톤 이슈 메모
- `docs/scratch/ux_infinite_skeleton_home_character_applied.md`: 적용 결과 메모(home/character)
- `docs/scratch/ux_infinite_skeleton_search_and_create_game.md`: search/create game 이슈 메모
- `docs/scratch/ux_infinite_skeleton_search_and_create_game_applied.md`: 적용 결과 메모(search/create game)
- `docs/scratch/world_chat_tree.md`: 월드 채팅 트리 구조 탐색 메모

### 2.8 tickets/

- `docs/tickets/README.md`: 티켓 시스템 규칙, 작성법, analysis/scratch 구분
- `docs/tickets/_TEMPLATE.md`: 티켓 표준 템플릿
- `docs/tickets/OrderForm.md`: 티켓 생성 보조 폼/프롬프트
- `docs/tickets/MS-01/BUG-001_character_cdn.md`: BUG-001 요구사항/범위/검증 기준
- `docs/tickets/MS-01/BUG-002_game_character_selection_not_applied.md`: BUG-002 요구사항/범위/검증 기준
- `docs/tickets/MS-01/BUG-003_persona_not_rendered_in_new_chat_sessions.md`: BUG-003 요구사항/범위/검증 기준
- `docs/tickets/MS-01/BUG-004_persona_modal_not_closing_on_new_session_character_world.md`: BUG-004 요구사항/범위/검증 기준
- `docs/tickets/MS-01/BUG-MyList-002-my-list-scope-and-empty-state-fix.md`: MyList-002 버그 티켓
- `docs/tickets/MS-01/BUG-MyList-003-my-list-navigation-routing-fix.md`: MyList-003 버그 티켓
- `docs/tickets/MS-01/BUG-MyList-004-my-create-placeholder-state-fix.md`: MyList-004 버그 티켓
- `docs/tickets/MS-01/UX-001 Persona Toast Message Unification.md`: UX-001 개선 티켓
- `docs/tickets/MS-03/FEAT-MyList-001-my-list-navigation-structure.md`: MyList 기능 티켓

---

## 3) AI 실행 흐름에서의 역할 설명

### 3.1 현재 docs를 AI 파이프라인으로 해석

현재 구조는 다음 6단계 파이프라인에 매핑된다.

1. 정책/가드레일
- 핵심 문서: `SSOT.md`, `ARCHITECTURE.md`, `AI_AGENT_RULES.md`
- 역할: "무엇이 허용/금지인지"를 선행 고정

2. 실행 프로토콜
- 핵심 문서: `AI_ENTRYPOINT.md`, `AI_DEV_PROMPT.md`, `DEVELOPMENT_GUIDE.md`
- 역할: "어떤 순서로 읽고, 어떤 형식으로 작업/보고할지"를 표준화

3. 작업 입력(요구사항)
- 핵심 문서: `tickets/README.md`, `tickets/_TEMPLATE.md`, `tickets/MS-*/...`
- 역할: 티켓 단위 요구사항/AC/검증 기준 제공

4. 구현 전후 증적
- 핵심 문서: `analysis/README.md`, `analysis/*_report.md`, `analysis/*_analysis.md`
- 역할: Root Cause -> 구현 -> 검증 결과를 추적 가능한 산출물로 고정

5. 검증/완료 판정
- 핵심 문서: `QA_AND_DONE.md`
- 역할: DONE 조건과 Human verification 경계 정의

6. 임시 탐색/운영 기록
- 핵심 문서: `scratch/*`, `logs/*`, `misc/*`
- 역할: 실험/디버깅/운영 히스토리 보관(비준거)

### 3.2 AI 개발 시스템 관점의 의미 있는 논리 구조

물리 폴더를 바꾸지 않고도, AI는 아래와 같이 "의미 계층"으로 해석해 사용하면 된다.

- Canonical Layer (의사결정 기준)
  - `SSOT.md`, `ARCHITECTURE.md`, `AI_AGENT_RULES.md`, `QA_AND_DONE.md`
- Execution Layer (실행 절차)
  - `AI_ENTRYPOINT.md`, `AI_DEV_PROMPT.md`, `DEVELOPMENT_GUIDE.md`
- Task Layer (요구사항 입력)
  - `tickets/`
- Evidence Layer (출력/검증 증적)
  - `analysis/`
- Reference Layer (보조 참조)
  - `architecture/`, `infra/`
- Temporary/History Layer (비준거 기록)
  - `scratch/`, `logs/`, `misc/`

### 3.3 운영 제안 (구조 유지 전제)

현재 docs는 이미 AI 친화적으로 잘 분리되어 있다. 다만 실행 안정성을 위해 다음 규칙을 권장한다.

- 티켓 수행 시 읽기 우선순위는 항상 `SSOT -> ARCHITECTURE -> AI_AGENT_RULES -> DEVELOPMENT_GUIDE -> AI_ENTRYPOINT -> ticket -> related analysis`
- `scratch/` 문서가 재사용되는 순간 `analysis/` 또는 `architecture/`로 승격 후보로 표기
- `analysis/`의 파일명 규칙을 통일(`{TICKET-ID}_report.md` or 확장형)
- `logs/`는 일자형 유지, 티켓 참조 링크를 각 로그에 1줄 추가하면 추적성이 증가

---

## 결론

`docs/`는 이미 "티켓 기반 AI 개발 시스템"에 맞는 구조를 갖추고 있으며, 핵심은 폴더 재배치보다 **문서의 계층적 사용 규칙(준거 문서 우선, scratch 비준거 처리, analysis 증적 강제)** 을 일관되게 지키는 것이다.

