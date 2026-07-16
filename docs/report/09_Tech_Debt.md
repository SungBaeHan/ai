# 09. Tech Debt

> 현재 코드 기준 기술 부채 (2026-06-14)

---

## 1. 구조적 문제

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| Route 직접 Mongo 접근 | Usecase/Adapter 패턴 미적용 다수 | `game_turn.py`, `characters.py`, `games.py` | Route → Usecase → Adapter 이관 (`docs/USECASE_REFACTOR_ROADMAP.md`) |
| 채팅 이중 구조 | V2(`chat_*`) + 레거시(`characters_*`/`worlds_*`) 공존 | `chat_v2.py`, `chat_persist.py` | 단일 채팅 모델로 통합 |
| 프론트 이중 구조 | `web-html` + React 스캐폴드 | `html/app/web/` | SSOT 정리, 하나로 수렴 |
| `engine_input` 미사용 | 조립 후 LLM 미전달 | `game_turn.py` L348 | 삭제 또는 실제 사용 |
| 게임 상태 FSM 부재 | `phase` 저장만 | `game_turn.py`, `schemas/game_turn.py` | 명시적 전이 + guard |

---

## 2. 중복 코드

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| Ask 라우터 중복 | `ask.py` ≈ `app_api.py` | `app_api.py` | 미등록 파일 제거 |
| Chat 라우터 중복 | `chat.py` vs `app_chat.py` | `chat.py` | 테스트용 분리 또는 삭제 |
| JWT_SECRET 다중 정의 | 모듈별 기본값 상이 | `auth.py`, `auth_google.py` | `config.py` 단일화 |
| HP/MP 적용 로직 | `game_turn.py` vs `game_status_service.py` | 두 파일 | deprecated 제거, 단일 함수 |
| API_BASE 하드코딩 | HTML 페이지별 중복 | `my.html`, `home.html` 등 | `config.js`만 사용 |

---

## 3. 복잡한 함수/컴포넌트

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| `play_turn()` | 400줄+, 다중 책임 | `game_turn.py` | 이벤트/LLM/저장 분리 |
| `chat()` in app_chat | 인증·persist·LLM·후처리 혼재 | `app_chat.py` | 서비스 레이어 추출 |
| `game.html` | 2700줄+ 단일 파일 | `game.html` | JS 모듈 분리 |
| `create_game()` | 스냅샷·R2·rules·캐릭터 한 함수 | `games.py` | usecase 분리 |

---

## 4. 타입 안정성 문제

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| `updated_combat: Optional[Dict]` | 느슨한 타입 | `schemas/game_turn.py` | `CombatState` Pydantic 모델 |
| Mongo dict 직접 조작 | 스키마 drift | 다수 routes | 공식 스키마 + validator |
| `current_user` dict | 타입 불명확 | `deps/auth.py` | TypedDict / 모델 |

---

## 5. 에러 처리 부족

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| LLM JSON 실패 폴백 | 이벤트 데이터 소실 | `game_turn.py` | 재시도 또는 부분 파싱 |
| `items_add` 미적용 | 스키마만 존재 | `game_turn.py` | inventory 반영 |
| 몬스터 스냅샷 로드 TODO | DB→스냅샷 변환 누락 | `game_turn.py` L148 | 변환 구현 |
| 페르소나 적용 롤백 TODO | 실패 시 UI 불일치 | `game.html` | optimistic rollback |

---

## 6. 보안 리스크

| 항목 | 심각도 | 관련 파일 | 개선 방향 |
|------|--------|----------|----------|
| JWT_SECRET 기본값 | 높음 | `auth.py`, `auth_google.py` | 운영 env 필수 검증 |
| Google Client ID 하드코딩 | 중간 | `my.html` | env/설정 주입 |
| Debug/Ops 엔드포인트 공개 | 중간 | `debug_db.py`, `migrate.py` | 인증·IP 제한 |
| `AUTH_USER_INFO_V2_SECRET` 기본값 | 중간 | `config.py` | 운영 시 변경 필수 |
| CORS 하드코딩 | 낮음 | `main.py` | env 기반 (문서와 불일치) |

---

## 7. 테스트 부족

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| 테스트 파일 1개 | CORS만 | `tests/test_cors.py` | API·게임 턴·auth 통합 테스트 |
| LLM mock 없음 | E2E 어려움 | — | fixture + contract test |
| 프론트 테스트 | 없음 | `web-html/` | E2E (Playwright 등) |

---

## 8. 배포/운영 리스크

| 항목 | 설명 | 관련 파일 | 개선 방향 |
|------|------|----------|----------|
| QUICK_START outdated | web/ollama 안내 불일치 | `docs/QUICK_START.md` | compose 현행화 |
| PORT 불일치 | entrypoint 10000 vs compose 8000 | `docker-entrypoint.sh` | 문서·설정 통일 |
| Nginx conf vs README | 전체 프록시 vs /docs만 | `infra/nginx/` | 문서·설정 일치 |
| `characters_session` 인덱스 없음 | 성능·중복 위험 | `startup.py` | 인덱스 추가 |
| Stripe 미구현 | 결제 없음 | — | MVP 범위 결정 |

---

## P0/P1/P2 상세 (요청 형식)

## Route 직접 Mongo 접근

- **심각도:** P1
- **영향:** 테스트·유지보수 어려움, SSOT 패턴 이탈
- **근거 파일:** `game_turn.py`, `characters.py`, `games.py`, `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`
- **현재 상태:** 대부분 route에서 `get_db()` 직접 호출
- **개선 방향:** 신규 기능부터 Usecase→Adapter (`USECASE_REFACTOR_ROADMAP.md`)
- **MVP 전 필수 여부:** 아니오 (점진 이관)

## JWT_SECRET 기본값

- **심각도:** P0
- **영향:** 토큰 위조·세션 탈취
- **근거 파일:** `deps/auth.py`, `routes/auth_google.py`
- **현재 상태:** env 미설정 시 기본 문자열 사용
- **개선 방향:** startup 시 운영 env 필수 검증
- **MVP 전 필수 여부:** **예**

## LLM JSON 파싱 실패 폴백

- **심각도:** P0
- **영향:** 턴 진행은 되나 HP/전투 상태 불일치
- **근거 파일:** `game_turn.py`
- **현재 상태:** narration-only fallback, delta=0
- **개선 방향:** 재시도, structured output, 부분 파싱
- **MVP 전 필수 여부:** **예** (데모 품질)

## Debug/Ops 엔드포인트 공개

- **심각도:** P0
- **영향:** DB 정보·마이그레이션 노출
- **근거 파일:** `main.py`, `debug_db.py`, `migrate.py`
- **현재 상태:** 인증 없이 접근 가능
- **개선 방향:** IP allowlist 또는 admin auth
- **MVP 전 필수 여부:** **예**

## rules 저장 vs LLM 미전달

- **심각도:** P1
- **영향:** 사용자 설정 룰이 플레이에 반영 안 됨
- **근거 파일:** `games.py`, `game_turn.py`, `trpg_game_master.py`
- **현재 상태:** `games.rules` 저장만, events 확률만 서버 사용
- **개선 방향:** rules 요약 프롬프트 주입 또는 서버 판정
- **MVP 전 필수 여부:** 부분 (MVP에서 rules UI 숨기거나 문서화)

## 테스트 1파일 (CORS만)

- **심각도:** P1
- **영향:** 회귀 미탐지
- **근거 파일:** `tests/test_cors.py`
- **현재 상태:** 통합 테스트 없음
- **개선 방향:** auth, games, turn smoke tests
- **MVP 전 필수 여부:** 권장 (수동 QA로 대체 가능)

## 문서/코드 불일치 (QUICK_START, CORS env)

- **심각도:** P2
- **영향:** 온보딩 지연
- **근거 파일:** `docs/QUICK_START.md`, `main.py`
- **현재 상태:** compose·포트·CORS 설명 불일치
- **개선 방향:** 문서 현행화 또는 코드 env 연동
- **MVP 전 필수 여부:** 아니오

---

## 분석 기준 파일

- `apps/api/routes/`, `docs/USECASE_REFACTOR_ROADMAP.md`
- `docs/architecture/ROUTES_DIRECT_MONGO_ACCESS.md`
- `docs/analysis/trpg-*.md`, `tests/`
