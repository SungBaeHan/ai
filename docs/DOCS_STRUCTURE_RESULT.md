# 문서 구조 정리 작업 결과

이번 docs/ 구조 정리 작업의 최종 결과 요약이다. 상세 변경 내역은 docs/DOCS_STRUCTURE_CHANGELOG.md 참고.

---

## 1. 수정한 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| **docs/SSOT.md** | Canonical Documentation, AI Reading Order, Documentation Structure Lock 섹션 추가 |
| **docs/AI_ENTRYPOINT.md** | 읽기 순서를 SSOT와 동일하게 정리(5→6→7 추가), 문서 구조 규칙 문구 추가 |
| **docs/AI_AGENT_RULES.md** | §16 Documentation Rules 추가 (doc 시스템/폴더 신설 금지, analysis/scratch 역할, scratch 승격 시 권고만) |
| **docs/DEVELOPMENT_GUIDE.md** | ROUTES 참조를 `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`로 변경, "Ticket Workflow: Analysis vs Scratch" 및 구조 변경 비범위 명시 추가 |
| **docs/ARCHITECTURE.md** | `docs/scratch/ROUTES_DIRECT_MONGO_ACCESS.md` → `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md` 로 참조 수정 |
| **docs/USECASE_REFACTOR_ROADMAP.md** | 동일 참조 2곳을 `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`로 수정 |
| **docs/architecture/DIRECTORY_STRUCTURE.md** | 상단에 reference/supplementary 안내 문구 추가 |
| **docs/architecture/CURRENT_FILE_STRUCTURE.md** | 상단에 reference/supplementary 안내 문구 추가 |
| **docs/architecture/REFACTORING_SUMMARY.md** | 상단에 reference/historical 안내 문구 추가 |
| **docs/tickets/README.md** | "Ticket vs Analysis vs Scratch" 섹션 추가, Ticket Naming에 underscore 예시(BUG-003) 추가 |
| **docs/tickets/OrderForm.md** | 상단에 "helper prompt/order form, not a ticket file" 안내 추가 |
| **docs/analysis/BUG-003-persona-not-rendered-in-new-chat-analysis.md** | 티켓 링크를 새 파일명 경로로 수정 |

---

## 2. 이동/통합/rename한 파일 목록

| 작업 | 상세 |
|------|------|
| **신규 생성** | **docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md** — roadmap 본문 표를 옮겨 refactor용 단일 참조 문서로 둠. scratch에는 원본이 없었음. |
| **신규 생성** | **docs/scratch/README.md** — scratch 용도·비준거성·승격 안내 |
| **신규 생성** | **docs/DOCS_STRUCTURE_CHANGELOG.md** — 이번 문서 구조 정리 요약 |
| **Rename** | `docs/tickets/MS-01/BUG-003 Persona Not Rendered in New Chat Sessions.md` → `docs/tickets/MS-01/BUG-003_persona_not_rendered_in_new_chat_sessions.md` (내용 동일, 새 경로에 작성 후 구 파일 삭제) |
| **삭제** | `docs/tickets/MS-01/BUG-003 Persona Not Rendered in New Chat Sessions.md` (위 rename 후 제거) |

**통합:** BUG-002 관련 scratch 문서는 현재 워크스페이스에 없어 통합/이동 없음. Changelog에 "manual review needed" 로 기록함.

---

## 3. 남겨둔 중복 문서 목록과 이유

| 문서 | 이유 |
|------|------|
| **docs/architecture/DIRECTORY_STRUCTURE.md** | 스냅샷/참고용. 상단에 "reference/supplementary" 문구 추가해 역할 명시. SSOT/ARCHITECTURE가 준거. |
| **docs/architecture/CURRENT_FILE_STRUCTURE.md** | 동일하게 스냅샷/참고용, 상단 안내 추가. |
| **docs/architecture/REFACTORING_SUMMARY.md** | 과거 리팩터 이력 참고용. 상단에 historical/reference 명시. |
| **docs/README.md** | 읽기 순서·scratch 언급 등이 있으나, 이번에 수정하지 않음. 최소 변경 원칙; SSOT가 준거이므로 나중에 README만 SSOT/구조 락으로 정리 가능. |

---

## 4. 추가 확인이 필요한 문서 목록

| 문서/항목 | 비고 |
|-----------|------|
| **BUG-002 관련 scratch** | 워크스페이스에 `BUG-002_FINAL_SUMMARY.md`, `BUG-002_FRONTEND_COMMIT_RENDER_PATH.md` 등 없음. 다른 브랜치/경로에 있으면 `docs/analysis/BUG-002_game_character_selection_not_applied_analysis.md`로 통합 검토 후, scratch 쪽 상단에 "formal analysis is in docs/analysis/..." 안내 권장. |
| **docs/README.md** | 현재 읽기 순서가 SSOT와 다를 수 있음. 필요 시 "Canonical reading order: see docs/SSOT.md" 한 줄로 정리 가능. |
| **docs/AI_DEV_PROMPT.md** | 이번에 수정하지 않음. 읽기 순서가 SSOT/AI_ENTRYPOINT와 다르면 추후 SSOT 기준으로 맞추는 것이 좋음. |

---

## 5. 최종 docs 구조 요약

```
docs/
├── SSOT.md                    ← 최상위 기준 (Canonical Documentation, AI Reading Order, Structure Lock 포함)
├── ARCHITECTURE.md            ← 시스템 구조 기준
├── AI_ENTRYPOINT.md           ← AI 시작 문서 및 읽기 순서 (SSOT와 동일)
├── AI_AGENT_RULES.md          ← AI 행동 규칙 (+ §16 Documentation Rules)
├── DEVELOPMENT_GUIDE.md      ← 개발 절차 (analysis/scratch 구분, ROUTES 참조 경로 정리)
├── DOCS_STRUCTURE_CHANGELOG.md ← 이번 정리 요약
├── DOCS_STRUCTURE_RESULT.md   ← 이번 작업 결과 (본 문서)
├── README.md, QUICK_START.md, USECASE_REFACTOR_ROADMAP.md, AI_DEV_PROMPT.md  ← 기타 (미수정)
├── tickets/                   ← 티켓·템플릿·OrderForm (README에 ticket/analysis/scratch 구분 명시)
│   ├── README.md
│   ├── _TEMPLATE.md
│   ├── OrderForm.md           ← 상단에 "helper prompt, not a ticket" 안내
│   └── MS-01/
│       ├── BUG-001_character_cdn.md
│       ├── BUG-002_game_character_selection_not_applied.md
│       └── BUG-003_persona_not_rendered_in_new_chat_sessions.md  ← rename됨
├── analysis/                  ← ticket-linked formal analysis
│   ├── BUG-003-persona-not-rendered-in-new-chat-analysis.md
│   └── repo_structure_analysis.md
├── architecture/              ← 보조 구조/스냅샷/리팩터 참고 (상단 안내 추가)
│   ├── DIRECTORY_STRUCTURE.md
│   ├── CURRENT_FILE_STRUCTURE.md
│   ├── REFACTORING_SUMMARY.md
│   └── ROUTES_DIRECT_MONGO_ACCESS.md  ← 신규 (기존 scratch 참조 대체)
├── infra/                     ← 인프라 문서 (미수정)
├── scratch/                   ← 임시/비준거 (README 신규)
│   └── README.md
├── logs/                      ← 일별 로그 (미수정)
└── misc/                      ← 기타 (미수정)
```

---

## Canonical reading order (SSOT 기준)

1. docs/SSOT.md  
2. docs/ARCHITECTURE.md  
3. docs/AI_AGENT_RULES.md  
4. docs/DEVELOPMENT_GUIDE.md  
5. docs/AI_ENTRYPOINT.md  
6. Assigned ticket under docs/tickets/  
7. Related formal analysis under docs/analysis/
