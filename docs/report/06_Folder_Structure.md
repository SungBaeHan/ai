# 06. Folder Structure

> 프로젝트 루트 `F:/git/ai` 기준 (2026-06-14)

---

## 상위 트리

```
ai/
├── apps/                    # 실행 애플리케이션
│   ├── api/                 # FastAPI 백엔드
│   ├── web-html/            # 프로덕션 정적 프론트
│   └── llm/                 # LLM 프롬프트
├── adapters/                # 외부 연동 구현
├── src/                     # 도메인·유스케이스·포트
├── infra/                   # Docker, Nginx, compose
├── docker/                  # Dockerfile
├── docs/                    # 프로젝트 문서
├── scripts/                 # 배포·마이그레이션·유틸
├── tests/                   # 테스트 (최소)
├── html/app/web/            # React 스캐폴드 (미배포)
├── assets/                  # 정적 에셋 (persona 등)
├── data/json/               # JSON 폴백 데이터
├── packages/                # 공유 패키지
├── requirements.txt
├── Dockerfile               # Render용
└── README.md
```

---

## `apps/api/` — Backend

| 경로 | 역할 |
|------|------|
| `main.py` | FastAPI 앱, 라우터 등록, CORS, 미들웨어 |
| `config.py` | 환경변수 Settings |
| `bootstrap.py` | 조기 env 로드 |
| `startup.py` | MongoDB 인덱스 |
| `routes/` | HTTP 라우터 (23파일) |
| `schemas/` | Pydantic 요청/응답 (`game_turn`, `chat_v2`, `user`) |
| `models/` | API 모델 (`games.py`) |
| `services/` | `game_events`, `chat_persist`, `logging_service`, `game_status_service`(deprecated) |
| `deps/` | `auth.py`, `user_snapshot.py` |
| `core/` | `user_info_token.py` |
| `utils/` | trace, image URL 등 |

---

## `apps/web-html/` — Frontend (프로덕션)

| 경로 | 역할 |
|------|------|
| `home.html` | 홈·캐릭터 목록 |
| `chat.html` | 캐릭터 채팅 |
| `world.html` | 세계관 채팅 |
| `game.html` | 게임 플레이 |
| `create/` | 캐릭터·세계관·게임 생성 |
| `my.html`, `my_list.html` | My 메뉴·리스트 |
| `personas.html` | 페르소나 관리 |
| `js/config.js` | API/CDN URL |
| `js/game_turn.js` | 게임 턴 헬퍼 |
| `static/js/session.js` | 세션 유틸 |

---

## `apps/llm/`

| 경로 | 역할 |
|------|------|
| `prompts/trpg_game_master.py` | 게임 턴 GM system/user 프롬프트 |

---

## `src/` — Clean Architecture (부분 적용)

| 경로 | 역할 |
|------|------|
| `domain/character.py` | Character 엔티티 |
| `usecases/character/` | list, get |
| `usecases/chat/` | open_chat, send_message |
| `usecases/rag/answer_question.py` | /v1/ask |
| `ports/repositories/` | Repository 인터페이스 |
| `ports/services/` | LLM, Embedding 인터페이스 |

---

## `adapters/`

| 경로 | 역할 |
|------|------|
| `persistence/mongo/` | MongoDB, repositories, chat adapter |
| `persistence/sqlite/` | SQLite 레거시 |
| `external/openai/` | OpenAI 클라이언트 |
| `external/llm_client.py` | LLM 팩토리 (OpenAI/Ollama) |
| `external/embedding/` | Sentence transformer |
| `file_storage/r2_storage.py` | Cloudflare R2 |

---

## `infra/`

| 경로 | 역할 |
|------|------|
| `docker-compose.yml` | api + qdrant |
| `docker-compose.reverse-proxy.yml` | Nginx |
| `docker-entrypoint.sh` | 컨테이너 시작 |
| `nginx/conf.d/` | Nginx site config |
| `README-OPERATIONS.md` | 운영 가이드 |

---

## `docs/`

| 경로 | 역할 |
|------|------|
| `01_~15_*.md` | 본 문서 세트 (신규 개발자용, TRPG/MVP 포함) |
| `SSOT.md`, `ARCHITECTURE.md` | 기존 SSOT·아키텍처 |
| `tickets/` | 티켓 |
| `analysis/` | 분석·구현 리포트 |
| `architecture/` | 구조 스냅샷 |
| `infra/` | Google 로그인 등 |

---

## `scripts/`

| 예시 | 역할 |
|------|------|
| `deploy_from_git.sh` | VM 배포 |
| `bootstrap_reverse_proxy.sh` | Nginx 기동 |
| `migrate_sqlite_to_mongo.py` | DB 마이그레이션 |
| `import_characters_from_json.py` | 데이터 임포트 |

---

## `html/app/web/` — React 스캐폴드

| 경로 | 역할 |
|------|------|
| `src/App.tsx` | 라우트 placeholder (`/my`만) |
| `src/pages/my/` | My 페이지 스텁 |

**상태:** `package.json` 없음, 프로덕션 미사용 (`docs/SSOT.md`)

---

## 신규 개발자가 먼저 볼 파일

| 순서 | 파일 | 이유 |
|------|------|------|
| 1 | `apps/web-html/js/config.js` | API URL·인증 헤더 |
| 2 | `apps/api/main.py` | 라우터 등록 전체 |
| 3 | `apps/api/routes/game_turn.py` | TRPG 핵심 루프 |
| 4 | `apps/api/routes/games.py` | 게임 생성·세션 |
| 5 | `apps/web-html/game.html` | 플레이 UI |
| 6 | `apps/llm/prompts/trpg_game_master.py` | GM 프롬프트 |
| 7 | `docs/SSOT.md` | 정책 SSOT |
| 8 | `docs/14_Code_Trace_Map.md` | FE→BE 추적표 |

---

## 수정 시 주의 파일

| 파일 | 주의 사항 |
|------|----------|
| `game_turn.py` | LLM·Mongo·이벤트 혼재, 회귀 위험 높음 |
| `game.html` | 2700줄+, HUD·채팅·페르소나 결합 |
| `auth.py` / `auth_google.py` | JWT 시크릿·세션 검증 |
| `main.py` | CORS·라우터 등록 누락 시 404 |
| `startup.py` | 인덱스 변경은 운영 DB에 영향 |
| `infra/nginx/` | API 경로·SSL 설정 |

---

## 분석 기준 파일

- `docs/architecture/DIRECTORY_STRUCTURE.md`, `docs/SSOT.md`
- 루트 및 `apps/`, `adapters/`, `src/` 디렉터리 listing
