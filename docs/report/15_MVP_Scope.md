# 15. MVP Scope

> 현재 구현 상태 기준 MVP 범위 재정의 (코드 기준, 2026-06-14)

---

## 1. MVP 목표 (코드에서 추론 가능한 범위)

README·SSOT 기준: **AI-Native TRPG 데모/MVP** — 세계관·캐릭터·게임 생성 후 AI GM과 턴 플레이·채팅.

공식 PRD 문서는 `docs/PRD/` 참조 (본 문서는 **코드 스냅샷** 기준).

---

## 2. 기능별 MVP 판정

| 기능 | MVP 포함 | 이유 | 현재 상태 | 남은 작업 | 리스크 |
|------|----------|------|----------|----------|--------|
| Google 로그인 | **예** | 사용자 식별 필수 | [x] | 운영 시크릿 점검 | JWT 기본값 |
| 캐릭터 목록/생성 | **예** | 핵심 콘텐츠 | [x] | — | 낮음 |
| 세계관 목록/생성 | **예** | 게임 전제 | [x] | — | 낮음 |
| 게임 생성 | **예** | TRPG 진입 | [x] | — | 낮음 |
| 게임 턴 플레이 | **예** | 핵심 차별점 | [~] | JSON 안정성, 몬스터 로드 | P0 |
| 캐릭터 TRPG 채팅 | **예** | 데모 시연 | [x] | — | 중간 |
| 세계관 채팅 | **예** | 데모 시연 | [x] | — | 중간 |
| 페르소나 | **예** | 채팅/게임 UX | [x] | session.js 경로 | 낮음 |
| My List / My Create | **예** | 사용자 가치 | [~] | Favorite API 없음 | P1 |
| HUD (HP/MP/Gold) | **예** | TRPG 느낌 | [x] | 인벤토리 미표시 | 낮음 |
| Rules UI | **예** | 생성 UX | [x] | 실행과 괴리 | P1 |
| Rules 실행 (주사위/데미지) | **아니오** | 미구현 | [ ] | 엔진 작업 | — |
| Stripe 결제 | **아니오** | planned only | [ ] | — | — |
| Admin UI | **아니오** | 없음 | [ ] | — | — |
| Chat V2 프론트 | **아니오** | V1으로 대체 가능 | [?] | 연결 확인 | — |
| RAG/Qdrant | **아니오** | 의도적 OFF | [ ] | — | — |
| React 프론트 | **아니오** | 미배포 | [ ] | — | — |
| 최근 플레이 캐릭터 | **아니오** | placeholder | [ ] | 후속 티켓 | — |
| 경험치/레벨 | **아니오** | 스키마 없음 | [ ] | — | — |
| 게임 종료 UI | **아니오** | 없음 | [ ] | — | — |

---

## 3. MVP 필수 기능 (최소 세트)

1. 로그인 (`my.html` + `auth_google`)
2. 홈 탐색 (`home.html`)
3. 캐릭터/세계관/게임 생성 (`create/*`)
4. 게임 플레이 (`game.html` + `/turn`)
5. 캐릭터 또는 세계관 채팅 1종 이상
6. API + MongoDB + OpenAI 운영 연결

---

## 4. MVP 제외 기능

- Stripe, Admin, RAG, Ollama(compose 비활성)
- Rules 수치 엔진 완성
- Chat V2 (프론트 미연결 시)
- My Favorite 데이터 백엔드
- 최근 플레이 기록

---

## 5. 오픈 전 필수 리스크 제거

| 항목 | 우선순위 |
|------|----------|
| `JWT_SECRET`, `AUTH_USER_INFO_V2_SECRET` 운영값 | P0 |
| `/_debug`, `/_ops/migrate` 접근 제한 | P0 |
| 게임 턴 JSON 폴백·몬스터 스냅샷 TODO | P0 |
| arcanaverse.ai ↔ api CORS/쿠키 교차 테스트 | P0 |
| Google Client ID 설정 (`my.html` 하드코딩 점검) | P1 |

---

## 6. Back Office 최소 범위

| 항목 | MVP |
|------|-----|
| Admin UI | **불필요** |
| Debug API 보호 | **필수** |
| MongoDB Atlas 접근 제한 | **필수** (인프라) |
| 로그 (`access_logs`, `error_logs`) | **권장** — 이미 구현 |

---

## 7. 운영 최소 범위

- Oracle VM + Docker API + Nginx
- Cloudflare Pages (프론트) + `api.arcanaverse.ai`
- MongoDB Atlas, OpenAI API, R2
- `dev` 브랜치 CI deploy (`deploy-dev.yml`)

---

## 8. 테스트 최소 범위

| 항목 | 현재 | MVP 최소 |
|------|------|----------|
| 자동 테스트 | `tests/test_cors.py` 1개 | CORS + auth smoke + turn API mock |
| 수동 QA | 티켓 Verification | 로그인→생성→게임 3턴→채팅 |

---

## 9. 보안 최소 범위

- 운영 시크릿 교체
- Debug/Ops 엔드포인트 차단
- HTTPS (Cloudflare Full strict)
- API 127.0.0.1 바인딩 + Nginx

---

## 10. AI/LLM 최소 검증

| 시나리오 | 필수 |
|----------|------|
| 게임 턴 JSON 파싱 성공률 | 예 |
| 파싱 실패 시 UX (폴백 narration) | 예 |
| TRPG 채팅 응답 품질 | 예 (수동) |
| 토큰 비용 상한 | 확인 필요 — 코드에 없음 |

---

## 11. 1인 개발 기준 현실적 출시 범위

**포함:** 위 MVP 필수 6항 + P0 리스크 제거 + 수동 QA 체크리스트  
**제외:** Rules 실행 엔진, Favorite API, Admin, 결제, Chat V2 UI

---

## 12. 출시 후 붙여도 되는 기능

- My Favorite 백엔드
- 최근 플레이 캐릭터
- items/inventory 적용
- phase FSM
- RAG
- Stripe
- 통합 테스트 확대

---

## MVP 판단

### 지금 바로 공개 가능 여부

**조건부 불가** — P0 보안·안정성(시크릿, debug 엔드포인트, 턴 JSON 안정성) 해결 전 **내부/데모 공개만 권장**.

### 공개 불가 시 핵심 이유

1. 운영 시크릿 기본값 잔존 가능
2. 무인증 debug/migrate API
3. 게임 턴 엔진 edge case (JSON 실패, 몬스터 스냅샷)

### 최소 공개 조건

- [ ] P0 보안 3항목 해결
- [ ] 프로덕션 env에서 로그인→게임 5턴 수동 QA 통과
- [ ] Oracle VM 배포 환경 검증 (`Release Verified`)

### 2주 내 목표 (제안)

- P0 전부 + 게임 턴 안정화 + My Favorite UI 정리(빈 상태 명시 또는 API)

### 4주 내 목표 (제안)

- items 적용, combat guard, 핵심 API 테스트 5개+, 문서-코드 동기화

### 중단 또는 방향 수정 기준

- LLM JSON 파싱 실패율이 수동 QA에서 **지속적으로 20% 초과** → structured output / function calling 검토
- 1인 개발로 Rules 엔진 + FSM + Favorite 동시 요구 시 → MVP 범위 재협의

---

## 분석 기준 파일

- `03_Feature_Index.md`, `12_Development_Status_Report.md`, `09_Tech_Debt.md`
- `apps/web-html/`, `apps/api/routes/`, `README.md`, `docs/SSOT.md`
