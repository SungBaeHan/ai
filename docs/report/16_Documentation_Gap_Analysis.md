# 16. Documentation Gap Analysis

> 감사 대상: 현재 체크아웃 브랜치 `main`의 소스와 `docs/report/00`–`10`, `12`–`15`  
> 감사일: 2026-07-17  
> 방식: Git 커밋 메시지는 시점 확인에만 사용했고, 기능 판정은 현재 소스의 라우터 등록·핸들러·프론트 파일·저장소 어댑터를 기준으로 했다. 실제 비밀값과 환경변수 값은 기록하지 않았다.

## 1. 기준 시점 및 범위

- **확인된 사실:** 감사 시작 시 작업 트리는 깨끗했고 현재 브랜치는 `main`이다. 보고서 세트는 커밋 `d656974`(2026-07-16, `report`)에서 한 번에 추가되었다. 그 직전 코드 커밋은 `d316b7e`(2026-04-09)이며, 2026-06-15 이후 코드 변경 커밋은 없다.
- **확인된 사실:** 반면 모든 대상 보고서는 본문에서 2026-06-14를 코드 기준일로 표기한다. 따라서 “문서 작성 시점”을 Git 추가 시점으로 볼 경우, 문서 뒤에 추가·변경된 코드는 없다. 본문 표기일을 기준으로 보더라도 이후 코드 커밋은 확인되지 않는다.
- **추정:** 2026-06-14는 실제 문서 생성일이 아니라 분석 기준일 또는 이전 산출물의 날짜일 가능성이 있다. Git 이력만으로는 확정할 수 없다.

## 2. 문서 기준일 이후 추가·변경된 코드와 기능

### 2.1 추가된 코드·기능

- **확인된 사실:** 없음. 2026-06-14 이후 `HEAD`까지 코드 변경 커밋은 없고, `d656974`의 변경은 보고서·분석 Markdown 파일 추가뿐이다.

### 2.2 변경된 코드·기능

- **확인된 사실:** 없음. 위와 같은 이유로 문서 기준일 이후의 실제 코드 동작 변경은 Git 이력에서 확인되지 않는다.

> 이 절의 “없음”은 현재 브랜치의 Git 이력을 기준으로 한 결론이다. 커밋되지 않은 작업, 다른 브랜치, 배포 환경의 설정·데이터 변경은 포함하지 않는다.

## 3. 문서에는 있으나 현재 코드에서 확인되지 않거나 코드와 다른 내용

| # | 구분 | 문서 내용 | 현재 코드 확인 결과 | 근거 | 판정 |
|---|---|---|---|---|---|
| 1 | 실제 동작 | API가 52개 엔드포인트라고 표기 | `main.py`에 등록된 라우터와 앱 라우트를 소스 데코레이터로 세면 60개 등록이다. `GET /health`는 앱과 health router에 중복 등록되어 method/path 기준 고유 수는 59개다. | 문서: `02_Architecture.md`, `04_API_Documentation.md`; 코드: `apps/api/main.py` L145–212, L391–407, `apps/api/routes/*.py`의 `@router.*` | **불일치 확인** |
| 2 | 실제 동작 | Users API를 `/v1/users`, `/v1/users/{user_id}`로 표기 | user router는 `main.py`에서 `prefix="/v1"`으로 등록되고, `apps/api/routes/user.py`의 데코레이터는 `""`, `"/{user_id}"`이다. 현재 경로는 `POST /v1`, `GET/PATCH/DELETE /v1/{user_id}`이다. | 문서: `04_API_Documentation.md` Users 절; 코드: `apps/api/main.py` L206, `apps/api/routes/user.py` L37, L77, L101, L133 | **불일치 확인** |
| 3 | 실제 동작 | 단순 질의 API를 `POST /v1/ask`로 표기 | 등록된 핸들러는 `ask_get`의 `GET ""`이며 main prefix를 합치면 `GET /v1/ask?q=`이다. API 문서(04)는 GET으로 맞지만 Feature Index(03)는 POST로 다르다. | 문서: `03_Feature_Index.md` Chat/단순 질의 행, `04_API_Documentation.md` Ask 절; 코드: `apps/api/main.py` L203, `apps/api/routes/ask.py` L74–80 (`ask_get`) | **문서 간·코드 간 불일치 확인** |
| 4 | 실제 동작 | RAG ask를 “compose만” 또는 전반적으로 비활성처럼 표현 | `/v1/ask`는 등록되어 있고 `answer()`가 `retrieve_context()`를 호출해 `QdrantClient.query_points()`를 실행한다. 단, `/v1/chat/`의 RAG 컨텍스트는 `context = ""`로 고정되어 있다. 즉 채팅 V1의 RAG OFF와 별도로 ask 경로는 코드상 활성이다. | 문서: `14_Code_Trace_Map.md` LLM/RAG ask 행, `03_Feature_Index.md`, `15_MVP_Scope.md`; 코드: `apps/api/routes/ask.py` L20–45, L74–80 (`retrieve_context`, `answer`, `ask_get`), `apps/api/routes/app_chat.py` L444–495 | **표현이 실제 동작을 과도하게 축소** |
| 5 | 참조/스키마 | Chat V2 저장소를 `chats_v2`로 표기 | Mongo 어댑터가 사용하는 컬렉션은 `chat_session`, `chat_message`, `chat_event`이다. `05_Database_Schema.md`와 `14_Code_Trace_Map.md`의 `chat_*` 표기는 코드와 부합하지만, `03_Feature_Index.md`의 `chats_v2`는 부합하지 않는다. | 문서: `03_Feature_Index.md` Chat V2 행, `05_Database_Schema.md` Chat V2 절; 코드: `adapters/persistence/mongo/chat_repository_adapter.py` L26–28, L242–295 | **문서 간·코드 간 불일치 확인** |
| 6 | 참조/프론트 | `character.html`, `my_create_characters.html`, `my_recent_characters.html`, `my_create_*.html` 화면을 연결 화면으로 표기 | 현재 `apps/web-html/`에는 해당 파일이 없다. 루트 HTML은 `chat.html`, `game.html`, `home.html`, `index.html`, `my.html`, `my_list.html`, `personas.html`, `search.html`, `world.html`이고 생성 화면은 `create/` 아래 3개다. | 문서: `03_Feature_Index.md` Character/My List 행, `14_Code_Trace_Map.md` My List 행; 코드: `apps/web-html/` 및 `apps/web-html/create/` 파일 목록 | **참조 불일치 확인** |
| 7 | 참조 | 페르소나 이미지 업로드 구현 파일을 `routes/uploads.py`로 표기 | 별도 `uploads.py`는 없고, `personas.py`의 `POST /uploads/persona-image` 핸들러가 구현체다. | 문서: `03_Feature_Index.md` Upload/Image 행; 코드: `apps/api/routes/personas.py` L462 (`upload_persona_image`), `apps/api/main.py` L207 | **참조 불일치 확인** |
| 8 | 참조 | Index에서 번호 문서를 `../01_Project_Overview.md` 등으로 링크하고, 본문에서도 `docs/01`–`docs/15`로 설명 | 실제 대상 파일은 `docs/report/` 아래에 있다. 현재 링크 대상인 `docs/01_Project_Overview.md` 등은 존재하지 않는다. | 문서: `00_Documentation_Index.md` 1.1, 6절 및 링크; 코드/트리: `docs/report/01_Project_Overview.md` 등 | **문서 링크 불일치 확인** |

## 4. 현재 코드에는 있으나 문서에 충분히 반영되지 않은 내용

| # | 내용 | 현재 코드 근거 | 문서 반영 상태 | 판정 |
|---|---|---|---|---|
| 1 | user router의 실제 공개 URL은 `/v1` 및 `/v1/{user_id}` | `apps/api/main.py` L206, `apps/api/routes/user.py` L37, L77, L101, L133 | `04_API_Documentation.md`가 `/v1/users...`로 기록하여 실제 URL이 반영되지 않았다. | **실제 동작 차이** |
| 2 | 등록 API는 60개(중복 `/health`를 제외한 고유 method/path 59개) | `apps/api/main.py`의 20개 `include_router` 및 3개 `@app.*`; 각 등록 라우터의 데코레이터 | `02`, `04`, `01`이 52개라고 표기한다. 세부 목록만으로 어떤 8개가 누락되었다고 단정하기보다, 집계 기준이 문서화되지 않은 상태다. | **집계 최신화 필요 사실** |
| 3 | Qdrant 검색을 실행하는 등록 API가 존재한다 | `apps/api/routes/ask.py`의 `retrieve_context`, `answer`, `ask_get`; `apps/api/main.py` L203 | V1 채팅의 OFF 상태와 혼재되어 RAG가 전반적으로 OFF/compose 전용인 것처럼 읽힌다. | **동작 범위 미반영** |

## 5. 문서 표현만의 차이와 실제 동작 차이

- **실제 동작 차이:** API 수 집계, Users URL prefix, Feature Index의 `/v1/ask` HTTP 메서드, ask 경로의 Qdrant 검색 가능 여부다. 호출자·클라이언트에 영향을 줄 수 있다.
- **표현/참조 차이:** Chat V2 컬렉션 명칭, 존재하지 않는 프론트/핸들러 파일명, Documentation Index의 상대 링크다. 코드 동작을 바꾸지는 않지만 추적·온보딩 정확도에 영향을 준다.
- **문서 내용이 현재도 부합하는 사례:** `rules`는 `engine_input["game_meta"]["ruleset"]`에 구성되지만 이 객체는 이후 LLM `messages`에 사용되지 않는다. 실제 프롬프트는 `build_trpg_user_prompt()`와 세션 텍스트로 구성된다. 따라서 “rules LLM 미전달”이라는 동작 결론은 현재도 맞고, 중간 객체 존재 여부만 문서에 생략되어 있다. 근거: `apps/api/routes/game_turn.py` L348–381, L418–454.

## 6. 판단 불가 또는 추가 확인 필요

| 항목 | 현재 판단 | 이유 및 근거 |
|---|---|---|
| 2026-06-14가 실제 문서 작성일인지 | 판단 불가 | 문서 본문 날짜와 Git의 보고서 추가일(2026-07-16)이 다르다. 외부 산출물·이관 이력이 없으면 어느 날짜가 작성일인지 확정할 수 없다. |
| OpenAPI에서 실제로 노출되는 최종 경로 수 | 소스상 60 등록/59 고유 경로로 확인, 런타임 확정은 추가 확인 필요 | FastAPI의 중복 `GET /health` 처리와 앱 기동 중 조건부 오류 여부는 실행한 OpenAPI `/openapi.json` 확인이 필요하다. 본 감사에서는 파일을 변경하거나 서비스 기동을 하지 않았다. |
| 프론트에서 Chat V2를 실제 호출하는지 | 현재 정적 프론트에서는 미확인 | `apps/web-html/`에서 `/chat/v2` 문자열을 확인하지 못했고, API는 `chat_v2.py`에 존재한다. 외부/별도 프론트 또는 배포된 번들은 이 저장소 코드만으로 배제할 수 없다. |
| 운영 배포, Cloudflare·MongoDB·Qdrant 연결 상태 | 판단 불가 | 저장소에는 설정·호출 코드만 있으며 실행 환경의 연결성, 데이터, 인덱스 생성 결과는 포함되지 않는다. |
| DB 스키마의 실제 저장 데이터 및 인덱스 상태 | 판단 불가 | 코드가 의도한 컬렉션/인덱스는 확인했지만, 운영 DB에 적용되었는지는 소스만으로 검증할 수 없다. |

## 7. 결과 요약

- **확정 핵심 차이점:** 9건 (실제 동작 4건, 참조·표현 4건, 기준 시점 추적성 1건)
- **문서 기준일 이후 확인된 코드 추가/변경:** 0건
- **추가 확인 필요:** 5건
