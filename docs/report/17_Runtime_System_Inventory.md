# Runtime System Inventory (current checkout)

## 조사 기준과 판정 방법

- 조사일: 2026-07-17
- 범위: 요청에 열거된 디렉터리와 실행/배포 설정. `docs/report` 및 기존 문서의 분석 결론, Git 커밋 메시지는 판정 근거로 사용하지 않았다.
- `실행 경로`는 `ENTRYPOINT`/compose 서비스, `apps.api.main`의 `include_router`, Python import, HTML의 script·`fetch`·페이지 링크를 따라 확인했다.
- 아래의 **확인됨**은 현재 체크아웃의 코드/설정에서 직접 확인한 사실이다. **추정/미확정**은 코드만으로 운영 상태를 단정할 수 없는 항목이다.
- API 수는 FastAPI 문서 UI 등 프레임워크 자동 경로를 제외한 **소스 등록 라우트 선언 수**다. `GET /health`가 두 번 등록되어 있으므로 61개 선언, 고유 method/path는 60개다.

## 1. 실행 가능한 애플리케이션과 진입점

| 구분 | 상태 | 진입점 및 근거 | 비고 |
|---|---|---|---|
| FastAPI API | 기본 실행 대상 | `infra/docker-entrypoint.sh`: `APP_MODULE` 기본값 `apps.api.main:app`, 마지막 `uvicorn "$APP_MODULE"`; `apps/api/main.py`: `app = FastAPI(...)` | Dockerfile과 compose 모두 이 entrypoint를 사용한다. |
| 진단 FastAPI | 조건부 대체 실행 대상 | `apps/diag/app.py`: `app = FastAPI()`, `/diag/ping`, `/diag/env`; `infra/docker-entrypoint.sh`의 import probe 실패 시 `uvicorn apps.diag.app:app` | 주 애플리케이션 import 실패 시에만 실행된다. 독립 compose 서비스는 없다. |
| Qdrant | 활성 compose 인프라 서비스 | `infra/docker-compose.yml`의 `services.qdrant` | 애플리케이션 코드의 `/v1/ask`, `/v1/chat` 경로가 URL을 참조한다. |
| 정적 HTML 웹 | 코드상 실제 UI 묶음이나 현 compose에서 미기동 | `apps/web-html/*.html`; `infra/docker-compose.yml`의 `web` 서비스 전체가 주석 처리됨 | compose 주석은 Cloudflare Pages 제공을 설명하지만, 이 저장소에는 Pages 빌드/배포 설정이 없다. |
| React 웹 소스 | 실행 대상 연결 확인 불가 | `html/app/web/src/App.tsx` | `package.json`, 빌드 설정, Docker/compose 참조를 찾지 못했다. 따라서 현재 기본 웹 앱으로 판정하지 않는다. |

`Dockerfile`은 `infra/docker-entrypoint.sh`를 `/entrypoint.sh`로 복사해 사용하고, `render.yaml`도 이 Dockerfile을 웹 서비스의 이미지 정의로 지정한다. 반면 `docker/api.Dockerfile`은 API image 정의까지만 있고 명시 `ENTRYPOINT`/`CMD`가 없으며 compose가 `/app/infra/docker-entrypoint.sh`를 직접 지정한다.

## 2. 프로덕션/기본 실행 경로

### 확인된 API 경로

1. `infra/docker-compose.yml`의 활성 `api` 서비스가 `docker/api.Dockerfile`로 이미지를 만들고 `/app/infra/docker-entrypoint.sh`를 실행한다.
2. entrypoint는 기본적으로 `apps.api.main:app`을 import probe한 뒤 Uvicorn으로 기동한다. (`infra/docker-entrypoint.sh`)
3. `apps/api/main.py`는 router 등록, `/assets/persona`와 `/json` 정적 mount, startup index 초기화를 수행한다. (`app.include_router(...)`, `_on_startup`)
4. 외부 공개 프록시는 `infra/docker-compose.reverse-proxy.yml`의 `reverse-proxy`이며, `infra/nginx/conf.d/api.arcanaverse.ai.conf`의 `location /`가 `http://api:8000`으로 프록시한다.

### 포트에 관해 확인된 불일치

- entrypoint의 `PORT` 기본값과 최상위 `Dockerfile`의 `EXPOSE`는 `10000`이다. (`infra/docker-entrypoint.sh`, `Dockerfile`)
- 활성 compose는 `127.0.0.1:8000:8000`을 publish하고 healthcheck도 container `8000`을 검사한다. (`infra/docker-compose.yml`)
- 따라서 compose의 `.env`/`infra/.env`가 `PORT=8000`을 제공하는지에 따라 정상 연결 여부가 달라진다. 실제 환경 값은 기록하거나 판정하지 않았으므로, **코드만으로는 compose API가 실제 8000에서 수신하는지 확정할 수 없다.**

### 정적 웹 경로

- 과거/선택 가능한 Nginx 정적 웹 정의는 `docker/nginx.Dockerfile` 및 `docker/nginx.conf`에 있으나, 해당 Dockerfile은 Nginx 베이스와 config copy까지만 포함하고 정적 HTML을 image에 복사하지 않는다.
- `infra/docker-compose.yml`의 해당 `web` 서비스는 주석 처리돼 있다. 따라서 현재 기본 compose 실행 경로에는 정적 웹 서버가 없다.
- 프론트의 `apps/web-html/js/config.js`는 운영 호스트에서 API를 `https://api.arcanaverse.ai`, 그 외에서는 `http://localhost:8000`으로 선택한다. 이는 브라우저 코드의 호출 대상 근거이지, Cloudflare Pages가 실제 배포됐다는 증거는 아니다.

## 3. 실제 사용 프론트 페이지와 공통 JavaScript

### 실제 정적 UI 페이지: 12개

`apps/web-html/index.html`은 즉시 `home.html`로 redirect하는 진입 리디렉터이므로 페이지 수에서 제외했다. 나머지 12개는 상호 링크 또는 화면에서 생성하는 링크로 도달하며, API 호출이 있거나 명시적 UI 진입 역할을 한다.

| 페이지 | 직접 근거 | 주요 호출/역할 |
|---|---|---|
| `home.html` | nav 링크와 `fetch` | 캐릭터·세계관·게임 목록: `/v1/characters`, `/v1/worlds`, `/v1/games` |
| `search.html` | nav 링크와 `fetch` | 세 종류의 검색/목록 API |
| `my_list.html` | nav 링크와 `fetch` | `/api/my-create/characters`, `/v1/characters/my` 및 목록 API |
| `my.html` | nav 링크와 Google script | `/v1/auth/google`, `/v1/auth/validate-session`, `personas.html` 링크 |
| `personas.html` | `my.html` 링크와 `fetch` | persona preset/CRUD/upload API |
| `chat.html` | 목록 화면이 생성하는 캐릭터 링크, `fetch` | character 상세/bootstrap, persona, `/v1/chat/` |
| `world.html` | `home.html`/`search.html`가 생성하는 링크, `fetch` | world 상세/bootstrap, persona, `/v1/chat/` |
| `game.html` | `home.html`/`search.html`가 생성하는 링크, `fetch` | game 상세/session/persona/turn |
| `create/index.html` | nav 링크 | 세 생성 화면의 허브 |
| `create/character.html` | create hub 링크와 `fetch` | character AI detail/create |
| `create/world.html` | create hub 링크와 `fetch` | world AI detail/create |
| `create/game.html` | create hub 링크와 `fetch` | world/character 선택 및 game create |

공통 JavaScript 연결은 다음과 같다.

- `apps/web-html/js/config.js`: 거의 모든 페이지가 로드한다. `API_BASE_URL`, anon ID, 전역 `fetch` 헤더 보강, `/v1/logs/event` 및 `/v1/logs/error` 전송을 정의한다.
- `apps/web-html/js/assets.js`: `home.html`, `search.html`, `my_list.html`, `game.html`, `create/game.html`에서 로드하는 asset path 정규화 함수다.
- `apps/web-html/static/js/session.js`: persona 및 생성 페이지에서 세션 확인/접근 제어 helper로 로드한다.
- `apps/web-html/static/js/infinite-scroll.js`: home/search/create-game에서 무한 스크롤 controller를 제공한다.
- `apps/web-html/js/game_turn.js`: `game.html`에서 로드하며 `playGameTurn()`이 `/v1/games/{gameId}/turn`을 호출한다.

`html/app/web/src/App.tsx`에는 `/my`, `/my/personas` 두 React route가 정의돼 있으나, 정적 HTML에서 이 React bundle을 참조하지 않고 build 설정도 없다. 따라서 위 12개 정적 페이지와 별개인 **미연결 React scaffold 후보**다.

## 4. FastAPI에 등록된 라우터와 API 영역

`apps/api/main.py`의 `include_router`를 기준으로만 집계했다. 괄호 안은 등록 route 선언 수다.

| 최종 prefix/영역 | 등록 모듈 및 주요 route 함수 | 수 |
|---|---|---:|
| health | `routes/health.py`: `root`, `env_present`, `db_check`, `test_openai_chat` → `/health...` | 4 |
| debug | `routes/debug.py:mongo_ping` → `/v1/debug/mongo-ping`; `routes/debug_db.py:debug_db` → `/_debug/db` | 2 |
| assets | `routes/assets.py:list_images` → `/assets/images` | 1 |
| characters | `routes/characters.py`: `get_list`, `get_one`, `get_count`, `get_my_characters`, upload/AI/create/bootstrap | 8 |
| character session | `routes/character_sessions.py:apply_persona_to_character_session` | 1 |
| worlds | `routes/worlds.py`: bootstrap, upload, AI detail, create, list, get | 6 |
| world session | `routes/world_sessions.py:apply_persona_to_world_session` | 1 |
| games + turn | `routes/games.py`: create/list/persona/get/session/health; `routes/game_turn.py:play_turn` | 7 |
| legacy-style chat | `routes/app_chat.py:chat`, `reset`, `health` → `/v1/chat` | 3 |
| RAG ask | `routes/ask.py:health`, `ask_get` → `/v1/ask` | 2 |
| auth | `routes/auth.py:get_current_user`, `logout`, `validate_session`; `routes/auth_google.py:google_login` | 4 |
| users | `routes/user.py` CRUD, router 자체 prefix `/users`, main prefix `/v1` | 4 |
| personas | `routes/personas.py`: presets, 내 persona CRUD/default, image upload | 7 |
| chat v2 | `routes/chat_v2.py:open_chat`, `send_message` → `/chat/v2/{chat_type}/{entity_id}` | 2 |
| logging | `routes/logs.py:log_event`, `log_error` → `/v1/logs` | 2 |
| my-create | `routes/my_create.py`의 두 character list route → `/api/...` | 2 |
| migration | `routes/migrate.py:migrate_sqlite_to_mongo` → `/_ops/migrate/sqlite-to-mongo` | 1 |
| main 직접 route | `apps/api/main.py:root`, `health`, `test_openai_chat` | 3 |
| **합계** |  | **61** |

`routes/health.py:root`와 `apps/api/main.py:health`가 모두 `GET /health`를 등록한다. 따라서 위 합계는 실제 등록 선언 수이고, 중복을 합친 고유 method/path는 60개다. 정적 mount도 별도로 존재한다: `apps/api/main.py`의 `app.mount('/assets/persona', ...)`(디렉터리가 있을 때)와 `app.mount('/json', ...)`(디렉터리가 있을 때).

## 5. 현재 실행 흐름에 연결된 Domain / Usecase / Adapter

### 확인된 연결

- **Character Domain**: `src/domain/character.py:Character`는 `apps/api/routes/characters.py`에서 import되고, Mongo/SQLite character repository adapter 및 migration route에서도 사용된다.
- **Chat V2 Usecase**: `src/usecases/chat/open_chat.py:OpenChatUseCase`, `src/usecases/chat/send_message.py:SendMessageUseCase`는 `apps/api/routes/chat_v2.py:open_chat/send_message`에서 실제 생성·호출된다.
- **Chat ports/adapters**: 같은 route가 `MongoChatRepository` (`adapters/persistence/mongo/chat_repository_adapter.py`)와 `LLMServiceAdapter` (`adapters/external/llm_service_adapter.py`)를 의존성으로 생성한다. 후자는 `adapters/external/llm_client.py:get_default_llm_client`로 연결된다.
- **Character repository**: `apps/api/routes/characters.py`의 module-level `get_character_repo()`는 `adapters/persistence/factory.py`를 통해 기본 Mongo 또는 조건부 SQLite adapter를 선택한다. `apps/api/main.py`도 Mongo character repository factory를 import/생성한다.
- **Mongo**: 다수 route와 access/event/error logging이 `adapters/persistence/mongo/__init__.py:get_db` 또는 `mongo.factory:get_mongo_client`를 사용한다. startup의 `apps/api/startup.py:init_mongo_indexes`도 main startup hook에서 호출된다.
- **R2 object storage**: character/world/game/persona route의 `get_r2_storage()`가 `adapters/file_storage/r2_storage.py:R2Storage`를 lazy-create하여 image upload에서 사용한다.
- **LLM**: legacy chat/game turn/ask 및 chat v2 adapter는 `adapters/external/llm_client.py`로 연결된다. 기본 provider는 `apps/api/config.py:Settings.llm_provider`상 `openai`이며 `ollama` 선택 branch도 코드상 있다.

### 등록됐지만 현재 정상 처리까지는 보장되지 않는 흐름

- `/v1/ask`와 `/v1/chat`의 RAG retrieval, 그리고 legacy chat의 관련 code는 `adapters/external/embedding/sentence_transformer.py:embed`를 호출한다.
- 이 함수는 구현상 항상 `RuntimeError`를 발생시키며, `requirements.txt`에서도 `sentence-transformers`가 주석 처리돼 있다. 따라서 해당 API는 **등록/호출 가능 경로는 존재하나 임베딩이 필요한 정상 RAG 실행은 현재 코드 기준 불가**다. `ask.py`는 예외를 잡아 오류 문자열을 응답할 수 있고, `app_chat.py`의 결과는 호출 지점별 error handling에 좌우된다.

## 6. 실행 경로 미연결 후보 (10개)

아래는 파일 존재가 아니라, main 등록/import·Docker entrypoint·웹 참조를 검색해 활성 기본 경로와의 연결을 찾지 못한 후보다. CLI로 직접 실행 가능한 경우는 별도로 표기했다.

1. `apps/api/routes/chat.py` — `/v1/chat` test router를 정의하지만 `apps/api/main.py`가 import/include하지 않는다. 활성 `app_chat.py`와 같은 목적의 별도 구현이다.
2. `apps/api/routes/app_api.py` — ask router를 정의하지만 main이 `ask.py`를 등록하므로 미등록이다.
3. `apps/api/routes/ask_chat.py` — `if __name__ == '__main__': main()` CLI RAG/REPL이나 main/compose가 연결하지 않는다.
4. `src/usecases/character/get_character.py` — 정의는 있으나 production source import를 찾지 못했다.
5. `src/usecases/character/list_characters.py` — 정의는 있으나 production source import를 찾지 못했다.
6. `src/usecases/rag/answer_question.py` — 정의는 있으나 production source import를 찾지 못했다.
7. `adapters/external/embedding/sentence_transformer_adapter.py` — port adapter 구현이나 import/use를 찾지 못했다.
8. `packages/rag/embedder.py` 및 `packages/rag/ingest.py` — package import/entrypoint 연결을 찾지 못했다. `ingest.py`에는 `main(folder)`가 있으나 `__main__` 실행 연결도 없다.
9. `packages/db/__init__.py` — SQLite helper 복제 계열로 보이며 production import를 찾지 못했다. 실제 조건부 SQLite 경로는 `adapters/persistence/sqlite/`다.
10. `html/app/web/src/` — React route source 두 개는 있으나 build/package/serve 참조가 없다.

## 7. 레거시·실험·스캐폴드 의심 영역

이는 코드 구조와 직접 주석/연결 상태에 근거한 분류이며, 삭제 여부나 과거 사용 여부를 의미하지 않는다.

- `apps/api/routes/chat.py`: 함수 docstring이 test endpoint라고 명시하고, main 미등록이다.
- `apps/api/routes/app_api.py`: 현재 등록된 `ask.py`와 같은 `/health`, root ask route를 재정의하지만 main 미등록이다.
- `apps/api/routes/ask_chat.py`: 파일 자체가 CLI REPL (`argparse`, `if __name__ == '__main__'`)이다.
- `html/app/web/src/App.tsx`: 코드 주석에 placeholder/TODO가 있고, `/my`, `/my/personas`만 정의돼 있으며 빌드 연결도 없다.
- `apps/api/routes/migrate.py` 및 `scripts/migrate_*.py`, `scripts/import_characters_from_json.py`: migration/import 전용 entrypoint 또는 ops API이며 일반 프론트 호출을 찾지 못했다.
- `adapters/external/embedding/sentence_transformer.py`: 파일 주석과 구현이 임시 stub임을 명시한다.
- `docker/nginx.Dockerfile`/`docker/nginx.conf`의 정적 웹 제공 경로: compose `web` 서비스가 주석 처리되어 기본 실행에서 제외된다.
- `apps/api/services/game_status_service.py`: source import를 찾지 못해 미연결 후보 성격이 있으나, 단독 파일만으로 기능 분류를 확정할 수 없어 위 10개 수에는 포함하지 않았다.

## 8. Docker / Nginx / 배포 설정이 가리키는 대상

- `infra/docker-compose.yml`: 활성 대상은 `qdrant`와 `api`; `api`는 `trpg-api`, 내부 `8000`, Qdrant URL `http://qdrant:6333`이다. `ollama`와 `web`은 주석 처리됐다.
- `infra/docker-compose.reverse-proxy.yml`: 별도 `reverse-proxy` Nginx가 80/443을 열고 `app-net`에 연결된다.
- `infra/nginx/conf.d/api.arcanaverse.ai.conf`: HTTPS `location /`가 compose service 이름 `api:8000`으로 모든 요청을 proxy한다. 정적 웹을 제공하지 않는다.
- `docker/nginx.conf`: 다른 Nginx 구성으로 `/api/`만 FastAPI에 넘기고 나머지를 `home.html`로 fallback한다. 그러나 현재 reverse-proxy compose는 이 파일을 사용하지 않는다.
- `render.yaml`: `Dockerfile` 기반의 단일 웹 서비스와 `/health` health check를 선언한다. 이 경로는 최상위 Dockerfile의 기본 `APP_MODULE`을 따른다.
- `scripts/deploy_from_git.sh`: compose와 reverse-proxy compose를 순서대로 올리는 운영 보조 script다. 실제로 실행됐는지는 코드만으로 알 수 없다.

## 9. 외부 서비스 의존성

| 외부 대상 | 코드/설정 근거 | 사용 영역 |
|---|---|---|
| MongoDB | `adapters/persistence/mongo/__init__.py:get_client/get_db`, `requirements.txt`의 `pymongo`, `motor` | 주 저장소, auth/user/persona/game/chat/log |
| Qdrant | `infra/docker-compose.yml:qdrant`, `routes/ask.py`, `routes/app_chat.py` | RAG vector query (단, 현재 embed stub으로 정상 RAG 불가) |
| OpenAI API | `adapters/external/openai/openai_client.py`, `adapters/external/llm_client.py:OpenAILLMClient`, `requirements.txt` | LLM chat/AI detail/game turn/chat v2 |
| Ollama | `OllamaLLMClient`, `requirements.txt`; compose service는 주석 처리 | 선택 가능한 provider 코드. 현재 컨테이너 서비스 실행 근거 없음 |
| Google Identity tokeninfo / GIS | `routes/auth*.py`의 Google verification URL, `my.html`의 `accounts.google.com/gsi/client` | Google login/token 검증 |
| Cloudflare R2 / S3 API | `adapters/file_storage/r2_storage.py`, `requirements.txt:boto3` | 이미지 업로드 |
| 이미지 CDN | `apps/api/config.py:ASSET_BASE_URL`, `apps/web-html/js/config.js` | image public URL 구성 |
| Render / Cloudflare Pages | `render.yaml`, compose 주석 | 구성/주석상 대상. 실제 배포 활성 여부는 미확정 |

비밀키·토큰·인증서·환경 변수 값은 조사 결과에 포함하지 않았다.

## 10. 현재 코드만으로 판단할 수 없는 부분 (5개)

1. compose `api`의 실제 `PORT` 값과 그에 따른 8000 포트 정상 수신 여부 (`infra/docker-compose.yml`과 entrypoint 기본값이 다름).
2. MongoDB, Qdrant, OpenAI, Google, R2/CDN 각각의 실제 접근 가능성·자격 증명·데이터 존재 여부.
3. Cloudflare Pages 정적 웹이 실제로 어느 디렉터리/버전을 배포 중인지와 운영 URL에서 12개 HTML이 제공되는지.
4. `render.yaml` 기반 배포와 Oracle VM compose/reverse-proxy 배포 중 어느 경로가 현재 운영 중인지.
5. `APP_MODULE` 또는 DB/LLM provider 환경값에 의해 기본 경로가 변경됐는지, 그리고 import failure 시 diag fallback이 실제 발생한 적이 있는지.

## 최종 요약

- 실행 애플리케이션 수: **2개** — 기본 FastAPI API 1개와 import 실패 시 조건부 진단 FastAPI 1개. (Qdrant는 애플리케이션이 아닌 활성 인프라 서비스로 별도 분류.)
- 실제 사용 프론트 페이지 수: **12개** — `index.html` 리디렉터 제외.
- 등록 API 수: **61개 선언** / **60개 고유 method-path** — 중복 `GET /health` 1개 포함.
- 실행 경로 미연결 후보 수: **10개**.
- 추가 확인 필요 항목 수: **5개**.
