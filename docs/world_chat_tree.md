# World Chat 파일/폴더 트리 설계 문서

## 목적
이 문서는 현재 Character Chat 구현 구조를 분석하고, 동일한 패턴으로 World Chat 모듈을 추가하기 위한 권장 파일/폴더 트리를 제시합니다.

---

## 1. 현재 Character Chat 관련 파일 목록

### 1.1 Repository 계층
- **인터페이스**: `src/ports/repositories/chat_repository.py`
  - 범용 `ChatRepository` 인터페이스 (chat_type을 파라미터로 받음)
  - `get_session`, `upsert_session`, `update_session`, `list_messages`, `insert_message`, `insert_event` 메서드 정의

- **어댑터**: `adapters/persistence/mongo/chat_repository_adapter.py`
  - `MongoChatRepository` 클래스 (범용 구현체)
  - `chat_session`, `chat_message`, `chat_event` 컬렉션 사용 (범용)
  - `ensure_indexes()` 정적 메서드 포함

### 1.2 Usecase 계층
- `src/usecases/chat/open_chat.py`
  - `OpenChatUseCase` 클래스 (범용, chat_type 파라미터 사용)
- `src/usecases/chat/send_message.py`
  - `SendMessageUseCase` 클래스 (범용, chat_type 파라미터 사용)

### 1.3 Schema 계층
- `apps/api/schemas/chat_v2.py`
  - 범용 스키마: `SessionSummary`, `Message`, `ChatEvent`
  - 범용 DTO: `OpenChatResponse`, `SendMessageRequest`, `SendMessageResponse`

### 1.4 Service 계층 (Character Chat 전용)
- `apps/api/services/chat_persist.py`
  - `persist_character_chat()` 함수
  - `characters_session`, `characters_message`, `characters_event` 컬렉션 직접 사용
  - `/v1/chat/` 엔드포인트에서 호출

### 1.5 Router 계층
- `apps/api/routes/characters.py`
  - `GET /v1/characters/{character_id}/chat/bootstrap` 엔드포인트
  - `bootstrap_character_chat()` 함수
  - `characters_session`, `characters_message` 컬렉션 직접 사용

- `apps/api/routes/chat_v2.py` (범용 라우터)
  - `GET /chat/v2/{chat_type}/{entity_id}` 엔드포인트
  - `POST /chat/v2/{chat_type}/{entity_id}/messages` 엔드포인트
  - 현재 사용되지 않는 것으로 보임 (Character Chat은 직접 MongoDB 접근)

- `apps/api/routes/app_chat.py`
  - `POST /v1/chat/` 엔드포인트
  - `persist_character_chat()` 함수 호출

### 1.6 Startup/초기화
- `apps/api/startup.py`
  - `init_mongo_indexes()` 함수에서 `MongoChatRepository.ensure_indexes()` 호출
  - 범용 `chat_session`, `chat_message`, `chat_event` 인덱스 생성

### 1.7 사용되는 MongoDB 컬렉션
- `characters_session`: 캐릭터 채팅 세션
- `characters_message`: 캐릭터 채팅 메시지
- `characters_event`: 캐릭터 채팅 이벤트

**참고**: 범용 `chat_session`, `chat_message`, `chat_event` 컬렉션도 존재하지만, Character Chat은 전용 컬렉션을 사용합니다.

---

## 2. World Chat 권장 트리 (신규 생성)

### 2.1 Service 계층 (신규)
```
apps/api/services/
  chat_persist.py                    # 기존 파일에 함수 추가
    + persist_world_chat()           # World Chat 저장 함수
```

**역할**: World Chat 저장 로직 캡슐화
- `worlds_session`, `worlds_message`, `worlds_event` 컬렉션 사용
- `persist_character_chat()` 패턴을 따라 구현
- 동일한 trace_id 로깅 및 upsert 패턴 유지

### 2.2 Router 계층 (기존 파일 확장)
```
apps/api/routes/
  worlds.py                          # 기존 파일에 엔드포인트 추가
    + bootstrap_world_chat()         # GET /v1/worlds/{world_id}/chat/bootstrap
```

**역할**: World Chat 재개 엔드포인트
- `bootstrap_character_chat()` 패턴을 따라 구현
- `worlds_session`, `worlds_message` 컬렉션 사용
- 인증: `get_current_user_v2` 사용

### 2.3 MongoDB 컬렉션 (신규)
```
worlds_session                      # World Chat 세션
worlds_message                      # World Chat 메시지
worlds_event                        # World Chat 이벤트
```

**스키마**: Character Chat과 동일
- `worlds_session`: `user_id`, `chat_type="world"`, `entity_id=world_id`, `status`, `updated_at`, `last_message_at`, etc.
- `worlds_message`: `session_id`, `user_id`, `role`, `content`, `created_at`, `request_id`, `meta`
- `worlds_event`: `session_id`, `user_id`, `event_type`, `payload`, `created_at`, `message_id`

### 2.4 인덱스 생성 (신규 함수 추가)
```
adapters/persistence/mongo/
  chat_repository_adapter.py        # 기존 파일에 메서드 추가
    + ensure_world_chat_indexes()   # World Chat 전용 인덱스 생성
```

**또는**

```
apps/api/startup.py                 # 기존 파일에 함수 추가
  init_mongo_indexes()
    + ensure_world_chat_indexes()   # World Chat 인덱스 생성 호출
```

**인덱스**:
- `worlds_session`: UNIQUE(`user_id`, `chat_type`, `entity_id`), (`user_id`, `updated_at` desc)
- `worlds_message`: (`session_id`, `created_at` asc), (`session_id`, `request_id`) partial unique
- `worlds_event`: (`session_id`, `created_at` desc), (`session_id`, `event_type`, `created_at` desc)

---

## 3. 수정 필요한 기존 파일 목록

### 3.1 Service 계층
**파일**: `apps/api/services/chat_persist.py`
- `persist_world_chat()` 함수 추가
- `persist_character_chat()` 패턴을 따라 구현
- 컬렉션명: `worlds_session`, `worlds_message`, `worlds_event`
- `chat_type="world"` 설정

### 3.2 Router 계층
**파일**: `apps/api/routes/worlds.py`
- `bootstrap_world_chat()` 함수 추가
- 엔드포인트: `GET /v1/worlds/{world_id}/chat/bootstrap?limit=50`
- `bootstrap_character_chat()` 패턴을 따라 구현
- 인증: `get_current_user_v2` 사용 (기존 패턴 유지)

**파일**: `apps/api/routes/app_chat.py` (선택사항)
- `/v1/chat/` 엔드포인트에서 World Chat 분기 추가
- `mode="world"` 또는 `chat_type="world"` 감지 시 `persist_world_chat()` 호출
- 현재는 Character Chat만 처리하는 것으로 보임

### 3.3 Startup/초기화
**파일**: `apps/api/startup.py`
- `init_mongo_indexes()` 함수에 World Chat 인덱스 생성 호출 추가
- `ensure_world_chat_indexes()` 함수 추가 (또는 `MongoChatRepository`에 메서드 추가)

**또는**

**파일**: `adapters/persistence/mongo/chat_repository_adapter.py`
- `ensure_world_chat_indexes()` 정적 메서드 추가
- `worlds_session`, `worlds_message`, `worlds_event` 인덱스 생성

### 3.4 Router 등록 (필요 시)
**파일**: `apps/api/main.py`
- World Chat 엔드포인트는 `worlds.router`에 추가되므로 별도 등록 불필요
- `app.include_router(worlds.router, prefix="/v1/worlds", tags=["worlds"])` 이미 존재

---

## 4. 파일/폴더 생성 요약

### 4.1 신규 생성 파일
**없음** (모두 기존 파일 확장)

### 4.2 기존 파일 수정
1. `apps/api/services/chat_persist.py`
   - `persist_world_chat()` 함수 추가

2. `apps/api/routes/worlds.py`
   - `bootstrap_world_chat()` 함수 추가
   - 엔드포인트 데코레이터 추가

3. `apps/api/startup.py` 또는 `adapters/persistence/mongo/chat_repository_adapter.py`
   - `ensure_world_chat_indexes()` 함수 추가
   - `init_mongo_indexes()`에서 호출

4. `apps/api/routes/app_chat.py` (선택사항)
   - World Chat 분기 추가 (현재 Character Chat만 처리)

---

## 5. 예상 엔드포인트

### 5.1 Bootstrap (재개)
- `GET /v1/worlds/{world_id}/chat/bootstrap?limit=50`
- 인증: `Authorization: Bearer <token>` (헤더)
- 응답: `{ "session": {...} | null, "messages": [...] }`

### 5.2 메시지 전송 (기존 `/v1/chat/` 확장)
- `POST /v1/chat/` (기존 엔드포인트)
- Body에 `mode="world"` 또는 `chat_type="world"` 포함
- `world_id` 포함

---

## 6. 구현 순서 권장

1. **인덱스 생성 함수 추가**
   - `ensure_world_chat_indexes()` 구현
   - `apps/api/startup.py`에서 호출

2. **Service 계층 추가**
   - `persist_world_chat()` 함수 구현
   - `persist_character_chat()` 패턴 복제

3. **Router 엔드포인트 추가**
   - `bootstrap_world_chat()` 함수 구현
   - `bootstrap_character_chat()` 패턴 복제

4. **기존 `/v1/chat/` 확장** (선택사항)
   - World Chat 분기 추가
   - `persist_world_chat()` 호출

5. **테스트**
   - Bootstrap API 호출 테스트
   - 메시지 저장/조회 테스트
   - 인덱스 생성 확인

---

## 7. TODO / 리스크

### 7.1 TODO
- [ ] `ensure_world_chat_indexes()` 함수 구현
- [ ] `persist_world_chat()` 함수 구현
- [ ] `bootstrap_world_chat()` 엔드포인트 구현
- [ ] `/v1/chat/` 엔드포인트에 World Chat 분기 추가 (선택)
- [ ] 프론트엔드 `world.html`에 bootstrap 호출 추가
- [ ] 통합 테스트 작성

### 7.2 리스크
1. **컬렉션 분리**: Character Chat은 `characters_*` 컬렉션을 사용하지만, 범용 `ChatRepository`는 `chat_*` 컬렉션을 사용함. World Chat도 전용 컬렉션(`worlds_*`)을 사용할지, 범용 컬렉션을 사용할지 결정 필요.
   - **권장**: Character Chat 패턴을 따라 `worlds_*` 전용 컬렉션 사용

2. **Repository 재사용**: `MongoChatRepository`는 범용 컬렉션을 사용하므로, World Chat 전용 컬렉션을 사용하려면 별도 어댑터나 서비스 함수가 필요함.
   - **현재 구조**: Character Chat도 `ChatRepository`를 사용하지 않고 직접 MongoDB 접근 (`chat_persist.py`)
   - **권장**: World Chat도 동일한 패턴 유지 (직접 MongoDB 접근)

3. **인덱스 관리**: Character Chat 인덱스는 `MongoChatRepository.ensure_indexes()`에서 범용 컬렉션 인덱스를 생성함. World Chat 전용 컬렉션 인덱스는 별도 함수 필요.
   - **권장**: `ensure_world_chat_indexes()` 함수 추가

4. **LLM Service**: World Chat도 동일한 `LLMService` 인터페이스 사용 가능 (기존 `LLMServiceAdapter` 활용)

---

## 8. 참고: Character Chat과의 차이점

### 8.1 공통점
- 동일한 세션/메시지/이벤트 구조
- 동일한 인증 방식 (`get_current_user_v2`)
- 동일한 스키마 (범용 `SessionSummary`, `Message`, `ChatEvent`)

### 8.2 차이점
- 컬렉션명: `characters_*` vs `worlds_*`
- 엔드포인트 prefix: `/v1/characters/` vs `/v1/worlds/`
- entity_id: `character_id` vs `world_id`

---

## 9. 디렉토리 구조 다이어그램

```
apps/api/
  services/
    chat_persist.py              # + persist_world_chat()
  routes/
    worlds.py                    # + bootstrap_world_chat()
    app_chat.py                  # (선택) World Chat 분기 추가
  startup.py                     # + ensure_world_chat_indexes() 호출

adapters/persistence/mongo/
  chat_repository_adapter.py     # (선택) + ensure_world_chat_indexes()

MongoDB Collections:
  worlds_session                 # 신규
  worlds_message                 # 신규
  worlds_event                   # 신규
```

---

**작성일**: 2025-01-XX  
**작성자**: Cursor AI  
**버전**: 1.0

