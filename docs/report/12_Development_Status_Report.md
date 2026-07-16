# 12. Development Status Report

> 프로젝트 현황 요약 (코드 기준, 2026-06-14)

---

## 1. Executive Summary

Arcanaverse TRPG MVP는 **핵심 플레이 루프(생성 → 게임 턴 → 채팅)** 가 동작하는 상태이다.  
프로덕션 프론트는 `apps/web-html/`, API는 FastAPI + MongoDB + OpenAI 구조이다.  
아키텍처 목표(Route→Usecase→Adapter)는 **부분 적용**이며, 결제·Admin·완전한 전투 FSM은 **미구현**이다.

---

## 2. 완료된 것

| 영역 | 내용 |
|------|------|
| 인증 | Google OAuth, JWT, user_info_v2, validate-session |
| 콘텐츠 CRUD | 캐릭터·세계관·게임 생성/조회 |
| 게임 플레이 | 턴 API, LLM JSON, HUD, 채팅 로그, 세션 persist |
| 채팅 | TRPG/QA `/v1/chat/`, bootstrap, persona 적용 |
| 페르소나 | CRUD, 프리셋, 세션 연동 |
| 에셋 | R2 업로드, CDN URL |
| My | My 메뉴, My List, My Create API |
| 인프라 | Docker API, Nginx, Cloudflare 배포 경로 |
| 로깅 | access/event/error logs |
| 문서·티켓 | SSOT, 티켓 시스템, analysis 리포트 |

---

## 3. 부분 구현된 것

| 영역 | 완료 | 미완 |
|------|------|------|
| 게임 전투 | in_combat, 랜덤 이벤트, LLM updated_combat | phase FSM, 서버 종료 판정, 몬스터 HUD |
| Rules | UI·DB 저장 | LLM 전달, 주사위/데미지 실행 |
| 아이템/인벤토리 | 스키마·프롬프트 | 턴 API 적용 |
| My Favorite | UI 탭 | 백엔드 favorites API |
| Chat V2 | API + usecase | 프론트 연결 확인 필요 |
| Clean Architecture | chat_v2, character usecase | 대부분 route 직접 Mongo |
| RAG/Qdrant | compose에 qdrant | 채팅에서 비활성 |
| React 프론트 | 스캐폴드 | 빌드·배포 없음 |
| 테스트 | CORS 테스트 | API·E2E 부족 |

---

## 4. 미구현

| 항목 | 근거 |
|------|------|
| Stripe 결제 | README/SSOT planned only |
| Admin / Back Office | 라우트·UI 없음 |
| 경험치(exp) | 스키마 없음 |
| 게임 명시적 종료 | UI·API 없음 |
| 탐험/대화 모드 state | combat boolean만 |
| 이메일 로그인 | 없음 |
| 최근 플레이 캐릭터 데이터 | placeholder UI만 |

---

## 5. MVP에 필요한 것 (코드 갭 기준)

| 우선순위 | 항목 |
|----------|------|
| P0 | 운영 시크릿·debug 엔드포인트 보호 |
| P0 | 게임 턴 안정성 (JSON 폴백, 몬스터 스냅샷) |
| P1 | 전투 상태 일관성 (종료 검증, 이벤트 중복 방지) |
| P1 | My Favorite 또는 MVP 범위에서 UI 제거/명시 |
| P1 | 핵심 API 통합 테스트 |
| P1 | `items_add` 등 스키마-적용 정합 |

---

## 6. MVP에서 제외해도 되는 것

| 항목 | 이유 |
|------|------|
| Stripe | SSOT에서 planned, 코드 없음 |
| Admin UI | 운영은 debug API로 대체 가능 (임시) |
| RAG/Qdrant | 의도적 OFF |
| React 프론트 | 프로덕션 미사용 |
| Ollama | compose 비활성 |
| Chat V2 (프론트 미연결 시) | 레거시 chat으로 대체 가능 |
| SQLite | mongo 기본 |

---

## 7. 출시 전 반드시 확인할 리스크

| 리스크 | 심각도 | 확인 방법 |
|--------|--------|----------|
| JWT/시크릿 기본값 | 높음 | 운영 env audit |
| Google Client ID 노출/고정 | 중간 | `my.html` 설정 |
| Debug/Migrate 공개 | 중간 | 네트워크·인증 점검 |
| LLM JSON 파싱 실패 | 중간 | 턴 플레이 스트레스 테스트 |
| 전투 상태 LLM-only 종료 | 중간 | in_combat stuck 시나리오 |
| Mongo 인덱스 부족 | 중간 | users/worlds/session 조회 성능 |
| CORS/도메인 설정 | 중간 | arcanaverse.ai ↔ api 교차 테스트 |
| 문서-실행 불일치 | 낮음 | QUICK_START vs compose |
| 테스트 커버리지 | 중간 | regression 수동 QA |

---

## 8. 메트릭 (코드 기준)

| 항목 | 값 |
|------|-----|
| API 엔드포인트 (등록) | ~52 |
| Mongo 컬렉션 | ~18 |
| 프로덕션 HTML 페이지 | 14 |
| 테스트 파일 | 1 (`test_cors.py`) |
| LLM 프롬프트 파일 | 1+ (`trpg_game_master.py` + inline) |

---

## 9. 전체 완성도 요약

| 영역 | 완성도 (코드 기준) | 근거 |
|------|-------------------|------|
| 인증·콘텐츠 CRUD | 높음 | route+UI 연결 완료 |
| TRPG 게임 턴 | 중간 | LLM JSON 동작, rules/FSM 미완 |
| 채팅 | 높음 | V1 완료, V2 프론트 미확인 |
| 아키텍처 정합 | 낮음 | direct Mongo 다수 |
| 운영·보안 | 중간 | 로깅 있음, debug API 노출 |
| 테스트 | 낮음 | CORS 1파일 |
| 문서 | 높음 | SSOT + 번호 문서 15종 |

---

## 10. MVP 가능 여부

**조건부 가능** — P0 리스크 제거 + 수동 QA 통과 시 **제한적 데모 공개** 가능.  
상용 오픈은 `QA_AND_DONE.md` Release Verified(Oracle VM) 기준 **미충족** 가능성 높음.

---

## 11. 운영·기술·AI·보안 리스크 (분류)

| 분류 | 대표 리스크 |
|------|------------|
| 운영 | compose/QUICK_START 불일치, PORT 혼선 |
| 기술 | direct Mongo, 이중 채팅 스택 |
| AI/LLM | JSON 파싱 실패, 서사-스탯 불일치, 토큰 예산 없음 |
| 보안 | JWT 기본값, 무인증 ops API |

---

## 12. 추천 다음 작업 순서

1. P0 보안 (시크릿, debug 차단)
2. `game_turn.py` 몬스터 스냅샷 + JSON 안정화
3. 수동 QA 체크리스트 (로그인→게임 5턴)
4. `items_add` 적용 또는 MVP에서 제외 명시
5. 핵심 API 테스트 3~5개
6. `14_Code_Trace_Map` 기준 usecase 이관 (신규만)

---

## 현실적 결론

### 현재 상태

Arcanaverse는 **AI TRPG 데모로서 핵심 가치(생성·턴·채팅)를 시연할 수 있는 단계**이다.  
엔진·rules·운영 hardening은 **프로덕션 수준 이전**이다.

### MVP까지 남은 핵심 작업

- P0 보안 3종 + 게임 턴 안정화 + 프로덕션 수동 QA

### 가장 큰 리스크

**LLM 구조화 응답 신뢰 + 서버 검증 부재** (`13_TRPG_Engine.md`)

### 다음 1주 작업

P0 보안, `game_turn.py` TODO(몬스터 스냅샷), Oracle VM 스모크 QA

### 다음 2주 작업

combat guard, Favorite MVP 정리, API smoke tests, `15_MVP_Scope` 재평가

### 중단/방향수정 기준

- LLM JSON 실패율이 QA에서 지속 20% 초과 → structured output 전환 검토
- 1인 개발로 Rules 엔진+FSM+Favorite 동시 요구 → MVP 범위 재협의 필수

---

## 분석 기준 파일

- `apps/api/`, `apps/web-html/`, `infra/`, `tests/`
- `docs/SSOT.md`, `docs/analysis/v1-recovery-status-report.md`
- `03_Feature_Index.md`, `09_Tech_Debt.md`, `10_TODO_and_Roadmap.md`
