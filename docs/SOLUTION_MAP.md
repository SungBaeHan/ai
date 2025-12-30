# 솔루션 맵 (Solution Map)

생성일: 2025-01-27

현재 레포지토리 기준으로 폴더별 역할, 의존성 흐름, 채팅 관련 코드 맵, MongoDB 접근 패턴을 정리한 문서입니다.

---

## 0-1. Top-level Tree

```
.
├── apps/                           # 애플리케이션 레이어
│   ├── api/                        # FastAPI REST API 서버
│   │   ├── routes/                 # API 엔드포인트 라우터
│   │   ├── services/               # 비즈니스 로직 서비스
│   │   ├── schemas/                # Pydantic 스키마
│   │   ├── models/                 # 데이터 모델
│   │   ├── dependencies/           # FastAPI 의존성
│   │   ├── deps/                   # 추가 의존성
│   │   ├── utils/                  # 유틸리티
│   │   ├── core/                   # 핵심 기능 (토큰 등)
│   │   ├── main.py                 # FastAPI 진입점
│   │   ├── config.py               # 설정
│   │   └── startup.py              # 초기화
│   ├── web-html/                   # 정적 HTML 프론트엔드
│   ├── core/                       # 공통 코어 유틸리티
│   ├── diag/                       # 진단 도구
│   └── llm/                        # LLM 프롬프트
├── src/                            # 도메인 레이어 (Clean Architecture)
│   ├── domain/                     # 도메인 엔티티
│   ├── ports/                      # 인터페이스 (Repository, Service)
│   └── usecases/                   # 유스케이스 (비즈니스 로직)
├── adapters/                       # 어댑터 레이어
│   ├── persistence/                # 데이터베이스 어댑터
│   │   ├── mongo/                  # MongoDB
│   │   ├── sqlite/                 # SQLite
│   │   └── factory.py              # Repository 팩토리
│   ├── external/                   # 외부 서비스 어댑터
│   │   ├── openai/                 # OpenAI 클라이언트
│   │   ├── embedding/              # 임베딩 서비스
│   │   └── llm_client.py           # LLM 클라이언트 추상화
│   └── file_storage/               # 파일 스토리지 (R2)
├── packages/                       # 공유 패키지
│   ├── rag/                        # RAG 관련
│   └── db/                         # DB 유틸리티
├── scripts/                        # 유틸리티 스크립트
├── infra/                          # 인프라 설정 (Docker Compose)
├── docker/                         # Docker 설정 파일
├── docs/                           # 프로젝트 문서
├── assets/                         # 정적 자산
├── data/                           # 데이터 파일
└── tests/                          # 테스트 코드
```

---

## 0-2. Layering (의존성 방향)

### 계층 구조 및 위치

| 계층 | 위치 | 역할 |
|------|------|------|
| **API 라우터** | `apps/api/routes/**` | HTTP 엔드포인트 처리, 요청 검증, 응답 생성 |
| **Service** | `apps/api/services/**` | 비즈니스 로직 (게임 세션, 이벤트 등) |
| **Repository/DB** | `adapters/persistence/**` | 데이터 접근 계층 (MongoDB, SQLite) |
| **Schema/Model** | `apps/api/schemas/**`, `apps/api/models/**` | Pydantic 스키마, 요청/응답 모델 |
| **Domain** | `src/domain/**` | 도메인 엔티티 (순수 비즈니스 객체) |
| **Use Cases** | `src/usecases/**` | 유스케이스 (도메인 로직) |
| **Ports** | `src/ports/**` | 인터페이스 정의 (Repository, Service) |
| **Adapters** | `adapters/**` | 외부 시스템 구현체 |
| **공통 유틸/설정** | `apps/api/utils/`, `apps/api/config.py`, `apps/api/dependencies/` | 공통 유틸리티, 설정, 의존성 |

### Import 의존성 방향

```
┌─────────────────────────────────────────────────────────┐
│                    apps/api/routes/                      │
│  (characters.py, games.py, game_turn.py, app_chat.py)   │
└────────────┬────────────────────────────────────────────┘
             │
             ├──→ apps/api/schemas/        (Pydantic 스키마)
             ├──→ apps/api/services/       (비즈니스 로직)
             ├──→ apps/api/utils/          (유틸리티)
             ├──→ apps/api/dependencies/   (인증 등)
             ├──→ adapters/persistence/factory.py  (Repository 팩토리)
             ├──→ adapters/persistence/mongo/      (직접 DB 접근)
             ├──→ adapters/external/       (LLM, Embedding)
             └──→ adapters/file_storage/   (R2 Storage)
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    apps/api/services/                    │
│  (game_session.py, game_events.py, game_status_service) │
└────────────┬────────────────────────────────────────────┘
             │
             └──→ adapters/persistence/mongo/  (DB 직접 접근)
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              adapters/persistence/mongo/                 │
│  (get_db(), get_client(), MongoCharacterRepository)     │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                  src/ports/repositories/                 │
│              (CharacterRepository 인터페이스)            │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                    src/usecases/                         │
│    (get_character.py, list_characters.py, answer_question) │
└────────────┬────────────────────────────────────────────┘
             │
             ├──→ src/domain/        (도메인 엔티티)
             └──→ src/ports/         (인터페이스)
```

### 의존성 방향 상세

```
routes → service → repository → db
  │        │         │
  ├→ schema          └→ schema
  └→ utils
```

**상세 흐름:**
1. **routes** → **schema**: 요청/응답 검증
2. **routes** → **service**: 비즈니스 로직 호출
3. **routes** → **repository factory**: Repository 인스턴스 획득
4. **routes** → **adapters/persistence/mongo**: 직접 DB 접근 (일부)
5. **service** → **adapters/persistence/mongo**: DB 접근
6. **repository** → **schema**: 데이터 변환
7. **usecases** → **domain**: 도메인 로직
8. **usecases** → **ports**: 인터페이스 의존

---

## 0-3. Existing Chat Related Code Map

### 캐릭터/세계관/게임 채팅 관련 파일 목록

#### 캐릭터 채팅
| 파일 | 역할 |
|------|------|
| `apps/api/routes/app_chat.py` | 캐릭터 채팅 API (`/v1/chat`), TRPG/QA 모드 지원 |
| `apps/api/routes/chat.py` | 테스트용 간단 채팅 API |
| `apps/api/routes/ask_chat.py` | RAG 기반 질문응답 채팅 (로컬 파일 히스토리) |

**주요 함수:**
- `chat()` (app_chat.py): 메인 채팅 엔드포인트, LLM 호출 및 응답 생성
- `get_or_create_sid()`: 세션 ID 생성/조회 (쿠키 기반)
- `build_messages()`: 메시지 히스토리 구성
- `postprocess_trpg()`: TRPG 모드 후처리

#### 게임 채팅 (턴 기반)
| 파일 | 역할 |
|------|------|
| `apps/api/routes/game_turn.py` | 게임 턴 처리 API (`/v1/games/{game_id}/turn`), LLM 기반 턴 진행 |
| `apps/api/services/game_session.py` | 게임 세션 유틸리티 (초기 캐릭터 정보 구성) |
| `apps/api/services/game_events.py` | 랜덤 이벤트 처리 (전투 등) |
| `apps/api/services/game_status_service.py` | 게임 상태 관리 |

**주요 함수:**
- `play_turn()` (game_turn.py): 게임 턴 진행, LLM 호출, 상태 업데이트
- `_convert_game_session_to_session_snapshot()`: MongoDB 문서 → 도메인 객체 변환
- `_convert_session_snapshot_to_game_session()`: 도메인 객체 → MongoDB 문서 변환
- `maybe_trigger_random_event()` (game_events.py): 랜덤 이벤트 판정
- `apply_event_to_session()`: 이벤트를 세션에 적용
- `build_initial_characters_info()` (game_session.py): 초기 캐릭터 정보 구성

#### 세계관 관련
| 파일 | 역할 |
|------|------|
| `apps/api/routes/worlds.py` | 세계관 CRUD API, 이미지 업로드 |
| `apps/api/routes/games.py` | 게임 생성/조회 API, 게임 메타데이터 관리 |

### 세션 저장/로드 처리 위치

#### 1. 캐릭터 채팅 세션 (`app_chat.py`)
- **저장 위치**: 메모리 딕셔너리 `SESSIONS` (전역 변수)
- **세션 키**: 쿠키 `sid` (UUID 기반)
- **저장 함수**: `get_or_create_sid()` - 세션 생성/조회
- **데이터 구조**: `SESSIONS[sid]["history_{mode}_{char_key}"]` - 캐릭터별 히스토리 리스트
- **TTL**: `SESSION_TTL = 60 * 60 * 6` (6시간)
- **초기화**: `/v1/chat/reset` 엔드포인트로 히스토리 초기화

```python
# apps/api/routes/app_chat.py
SESSIONS: Dict[str, Dict[str, Any]] = {}  # 메모리 저장
sid = get_or_create_sid(req)  # 쿠키에서 조회 또는 새로 생성
sess = SESSIONS[sid]
sess[key] = sess[key][-MAX_TURNS * 2:]  # 최근 3턴만 유지
```

#### 2. 게임 채팅 세션 (`game_turn.py`)
- **저장 위치**: MongoDB `game_session` 컬렉션
- **세션 키**: `game_id` + `owner_ref_info.user_ref_id` (복합 키)
- **저장 함수**: `db.game_session.update_one()` - MongoDB 업데이트
- **로드 함수**: `db.game_session.find_one()` - MongoDB 조회
- **데이터 구조**: 세션 스냅샷 (플레이어 상태, NPC 상태, 전투 상태, 스토리 히스토리)

```python
# apps/api/routes/game_turn.py
# 세션 로드
game_session = db.game_session.find_one({
    "game_id": game_id,
    "owner_ref_info.user_ref_id": user_id,
})

# 세션 저장
db.game_session.update_one(
    {"game_id": game_id, "owner_ref_info.user_ref_id": user_id},
    {"$set": updated_session},
)
```

#### 3. RAG 질문응답 (`ask_chat.py`)
- **저장 위치**: 로컬 파일 `.chat_history.json`
- **저장 함수**: `save_history()` - JSON 파일 쓰기
- **로드 함수**: `load_history()` - JSON 파일 읽기

```python
# apps/api/routes/ask_chat.py
HIST_PATH = Path(".chat_history.json")
save_history(history)  # JSON 파일로 저장
history = load_history(n_turns=8)  # 파일에서 로드
```

### 메시지 저장 위치

#### 캐릭터 채팅 메시지
- **저장**: 메모리 `SESSIONS[sid]["history_{mode}_{char_key}"]` 리스트
- **형식**: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
- **보존**: 최근 3턴 (MAX_TURNS * 2, user+assistant 쌍)

#### 게임 채팅 메시지
- **저장**: MongoDB `game_session.story_history` 배열
- **형식**: 턴 로그 리스트
  ```python
  {
      "turn": 1,
      "narration": "상황 설명",
      "dialogues": [
          {
              "speaker_type": "player|npc|monster|narration",
              "name": "...",
              "text": "...",
              "char_ref_id": "...",
              "is_action": false,
              "meta": {}
          }
      ]
  }
  ```
- **저장 위치**: `apps/api/routes/game_turn.py`의 `play_turn()` 함수 내부

#### RAG 질문응답 메시지
- **저장**: 로컬 파일 `.chat_history.json`
- **형식**: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`

### 상태(전투/스냅샷/이벤트) 저장 위치

#### 게임 상태 저장 (MongoDB `game_session` 컬렉션)
| 상태 항목 | 필드 경로 | 설명 |
|-----------|-----------|------|
| **플레이어 상태** | `user_info.attributes` | HP, MP, 속성값 |
| **플레이어 아이템** | `user_info.items` | 골드, 인벤토리 |
| **NPC 상태** | `characters_info[].snapshot.attributes` | 각 NPC의 HP, MP, 속성 |
| **전투 상태** | `combat` | 전투 여부, 몬스터 목록, 페이즈 |
| **스토리 히스토리** | `story_history[]` | 턴별 로그 (narration, dialogues) |
| **게임 스냅샷** | `world_snapshot` | 세계관 스냅샷 (games 컬렉션에서 참조) |
| **소유자 정보** | `owner_ref_info` | 사용자 ID, 게임 ID 등 |

#### 전투 상태 처리
- **위치**: `apps/api/services/game_events.py`
- **함수**: `maybe_trigger_random_event()`, `apply_event_to_session()`
- **저장**: `game_session.combat` 필드에 몬스터 목록, 전투 페이즈 등 저장

#### 이벤트 상태
- **랜덤 이벤트**: `game_turn.py`의 `play_turn()` 내부에서 매 턴 판정
- **이벤트 결과**: `game_session` 문서에 이벤트 정보가 스토리 히스토리에 기록

---

## 0-4. Mongo Access Pattern

### MongoDB Client 초기화 위치

#### 1. 싱글톤 패턴 (`adapters/persistence/mongo/__init__.py`)
```python
# adapters/persistence/mongo/__init__.py
_client: Optional[MongoClient] = None
_db: Optional[Database] = None

def get_client() -> MongoClient:
    """MongoDB 클라이언트 싱글톤"""
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        _client = MongoClient(mongo_uri)
    return _client

def get_db() -> Database:
    """MongoDB 데이터베이스 싱글톤"""
    global _db
    if _db is None:
        db_name = os.getenv("MONGO_DB", "arcanaverse")
        _db = get_client()[db_name]
    return _db
```

- **초기화 방식**: 지연 초기화 (lazy initialization)
- **접근**: `from adapters.persistence.mongo import get_db`
- **사용 위치**: 
  - `apps/api/routes/games.py`
  - `apps/api/routes/game_turn.py`
  - `apps/api/routes/worlds.py`
  - `apps/api/routes/characters.py`
  - `apps/api/routes/user.py`
  - `apps/api/routes/auth.py`
  - 기타 여러 라우터

#### 2. Repository 패턴 (`MongoCharacterRepository`)
```python
# adapters/persistence/mongo/character_repository_adapter.py
class MongoCharacterRepository(CharacterRepository):
    def __init__(self):
        self._uri = os.getenv("MONGO_URI")
        self._db_name = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB", "arcanaverse")
        self._client = None
        self._db = None
        self.collection = None
    
    def _ensure(self):
        if not self._client:
            self._client = MongoClient(self._uri, ...)
            self._db = self._client[self._db_name]
            self.collection = self._db["characters"]
```

- **초기화 방식**: 지연 초기화 (`_ensure()` 메서드)
- **접근**: `from adapters.persistence.factory import get_character_repo`

### Collection 접근 방식

#### 1. 직접 접근 (Direct Access)
**패턴**: `get_db()` → `db.collection_name` 직접 접근

**사용 예시:**
```python
# apps/api/routes/games.py
from adapters.persistence.mongo import get_db
db = get_db()
game_doc = db.games.find_one({"id": game_id})
db.game_session.update_one({...}, {...})
```

**접근되는 컬렉션:**
- `db.games` - 게임 메타데이터
- `db.game_session` - 게임 세션 상태
- `db.users` - 사용자 정보
- `db.worlds` - 세계관 정보

**위치**: 
- `apps/api/routes/games.py` (games, game_session)
- `apps/api/routes/game_turn.py` (game_session, games)
- `apps/api/routes/worlds.py` (worlds)
- `apps/api/routes/user.py` (users)
- `apps/api/routes/auth.py` (users)

#### 2. Repository 패턴 (Wrapper)
**패턴**: Repository 인터페이스를 통한 접근

**사용 예시:**
```python
# apps/api/routes/characters.py
from adapters.persistence.factory import get_character_repo
repo = get_character_repo()
character = repo.get_by_id(char_id)
characters = repo.list_all(offset=0, limit=30)
```

**접근되는 컬렉션:**
- `characters` - `MongoCharacterRepository`를 통해서만 접근

**위치**: `apps/api/routes/characters.py`

### Index 생성/초기화 코드 위치

#### 1. 서버 시작 시 인덱스 생성 (`apps/api/startup.py`)
```python
# apps/api/startup.py
def init_mongo_indexes() -> Optional[dict]:
    """Create commonly used indexes for Mongo collections."""
    from adapters.persistence.mongo import get_db
    db = get_db()
    
    # characters 컬렉션 인덱스
    if MongoCharacterRepository:
        repo = MongoCharacterRepository()
        col = repo.collection
        col.create_index("id", unique=True, name="uniq_id")
    
    # games 컬렉션 인덱스
    games_col = db.games
    games_col.create_index("id", unique=True, name="games_uniq_id")
    games_col.create_index("reg_user", name="games_idx_reg_user")
    games_col.create_index("world_ref_id", name="games_idx_world_ref_id")
    games_col.create_index("status", name="games_idx_status")
    
    # game_session 컬렉션 인덱스
    game_session_col = db.game_session
    game_session_col.create_index(
        [("game_id", 1), ("owner_ref_info.user_ref_id", 1)],
        name="game_session_idx_game_user"
    )
```

**호출 위치**: `apps/api/main.py`의 `@app.on_event("startup")` 훅
```python
# apps/api/main.py
@app.on_event("startup")
async def _on_startup():
    try:
        init_mongo_indexes()
    except Exception:
        pass
```

#### 2. 인덱스 목록

| 컬렉션 | 인덱스 | 타입 | 설명 |
|--------|--------|------|------|
| `characters` | `id` | Unique | 캐릭터 ID 고유 인덱스 |
| `games` | `id` | Unique | 게임 ID 고유 인덱스 |
| `games` | `reg_user` | Index | 등록 사용자 인덱스 |
| `games` | `world_ref_id` | Index | 세계관 참조 ID 인덱스 |
| `games` | `status` | Index | 게임 상태 인덱스 |
| `game_session` | `(game_id, owner_ref_info.user_ref_id)` | Compound | 게임+사용자 복합 인덱스 |

---

## 0-5. Output Format

### 1) Folder Purpose Table

| 폴더 | 목적 | 주요 파일/기능 |
|------|------|----------------|
| `apps/api/routes/` | API 엔드포인트 라우터 | HTTP 요청 처리, 검증, 응답 생성 |
| `apps/api/services/` | 비즈니스 로직 서비스 | 게임 세션, 이벤트, 상태 관리 |
| `apps/api/schemas/` | Pydantic 스키마 | 요청/응답 데이터 모델 |
| `apps/api/models/` | 데이터 모델 | 도메인 데이터 구조 |
| `apps/api/dependencies/` | FastAPI 의존성 | 인증, 사용자 정보 등 |
| `apps/api/utils/` | 유틸리티 | 공통 함수 |
| `apps/api/core/` | 핵심 기능 | 토큰 관리 등 |
| `src/domain/` | 도메인 엔티티 | 순수 비즈니스 객체 |
| `src/ports/` | 인터페이스 | Repository, Service 인터페이스 |
| `src/usecases/` | 유스케이스 | 비즈니스 로직 구현 |
| `adapters/persistence/mongo/` | MongoDB 어댑터 | DB 접근, Repository 구현 |
| `adapters/persistence/sqlite/` | SQLite 어댑터 | 개발용 DB 접근 |
| `adapters/external/` | 외부 서비스 어댑터 | LLM, Embedding 클라이언트 |
| `adapters/file_storage/` | 파일 스토리지 | R2 Storage 클라이언트 |

### 2) Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      apps/api/routes/                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ characters  │  │   games     │  │  game_turn  │            │
│  │   app_chat  │  │   worlds    │  │    auth     │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│         └────────────────┴────────────────┘                     │
│                        │                                        │
│         ┌──────────────┼──────────────┐                        │
│         │              │              │                        │
│    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                    │
│    │ schemas │   │services │   │  utils  │                    │
│    └─────────┘   └────┬────┘   └─────────┘                    │
│                       │                                        │
└───────────────────────┼────────────────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            │           │           │
    ┌───────▼──────┐  ┌▼─────────┐  ┌────────────┐
    │   Factory    │  │  Mongo   │  │  External  │
    │ (Repository) │  │  Direct  │  │  (LLM/R2)  │
    └───────┬──────┘  └──────────┘  └────────────┘
            │
    ┌───────▼──────┐
    │  Repository  │
    │ (Interface)  │
    └───────┬──────┘
            │
    ┌───────▼──────┐
    │   Use Cases  │
    └───────┬──────┘
            │
    ┌───────▼──────┐
    │    Domain    │
    └──────────────┘
```

### 3) Chat Flow Map

#### Character Chat Flow (`/v1/chat`)
```
HTTP Request
    ↓
apps/api/routes/app_chat.py::chat()
    ↓
get_or_create_sid() → SESSIONS[sid] (메모리)
    ↓
build_messages() → 히스토리 구성
    ↓
LLM 호출 (OpenAI)
    ↓
후처리 (postprocess_trpg, polish)
    ↓
SESSIONS[sid]["history_*"] 업데이트 (메모리)
    ↓
HTTP Response
```

**세션 저장**: 메모리 딕셔너리 `SESSIONS`
**메시지 저장**: `SESSIONS[sid]["history_{mode}_{char_key}"]` 리스트

#### Game Chat Flow (`/v1/games/{game_id}/turn`)
```
HTTP Request
    ↓
apps/api/routes/game_turn.py::play_turn()
    ↓
MongoDB: db.game_session.find_one() (세션 로드)
    ↓
랜덤 이벤트 판정 (maybe_trigger_random_event)
    ↓
이벤트 적용 (apply_event_to_session)
    ↓
LLM 호출 (OpenAI)
    ↓
JSON 파싱 및 상태 업데이트
    ↓
MongoDB: db.game_session.update_one() (세션 저장)
    ↓
HTTP Response
```

**세션 저장**: MongoDB `game_session` 컬렉션
**메시지 저장**: `game_session.story_history[]` 배열
**상태 저장**: `game_session.user_info`, `game_session.characters_info`, `game_session.combat`

#### World Chat Flow
세계관은 별도의 채팅 기능이 없으며, 게임을 통해 간접적으로 사용됩니다.

**관련 파일:**
- `apps/api/routes/worlds.py`: 세계관 CRUD
- `apps/api/routes/games.py`: 게임 생성 시 `world_snapshot` 저장

### 4) Risk Notes (import/순환/결합도)

#### 순환 참조 위험 지점

1. **`games.py` ↔ `game_turn.py`**
   - **위치**: `apps/api/routes/games.py` (line 619, 732)
   - **문제**: `games.py`에서 `game_turn.py`의 함수를 함수 내부에서 import
   - **해결책**: 함수 내부에서 import하여 순환 참조 방지 (현재 적용됨)
   ```python
   # 순환 import 방지를 위해 함수 내부에서 import
   from apps.api.routes.game_turn import _convert_game_session_to_session_snapshot
   ```

2. **`games.py` ↔ `personas.py`**
   - **위치**: `apps/api/routes/games.py` (line 691)
   - **문제**: `games.py`에서 `personas.py`의 함수를 함수 내부에서 import
   - **해결책**: 함수 내부에서 import (현재 적용됨)

#### 결합도 위험 지점

1. **Routes → MongoDB 직접 접근**
   - **위치**: `apps/api/routes/games.py`, `game_turn.py`, `worlds.py` 등
   - **문제**: Repository 패턴을 우회하여 직접 DB 접근
   - **위험도**: 중간 (유연성 감소, 테스트 어려움)
   - **개선 방안**: Repository 패턴으로 통일 고려

2. **Service → MongoDB 직접 접근**
   - **위치**: `apps/api/services/game_session.py` (간접적)
   - **문제**: Service 계층이 DB 직접 접근
   - **위험도**: 낮음 (현재는 주로 유틸리티 함수)

3. **메모리 세션 저장 (`app_chat.py`)**
   - **위치**: `apps/api/routes/app_chat.py`의 `SESSIONS` 전역 변수
   - **문제**: 서버 재시작 시 세션 손실, 멀티 인스턴스 환경에서 동기화 불가
   - **위험도**: 높음 (프로덕션 환경 문제)
   - **개선 방안**: Redis 또는 MongoDB로 마이그레이션 고려

4. **로컬 파일 세션 저장 (`ask_chat.py`)**
   - **위치**: `apps/api/routes/ask_chat.py`의 `.chat_history.json`
   - **문제**: 파일 시스템 의존, 멀티 인스턴스 환경에서 동기화 불가
   - **위험도**: 높음 (프로덕션 환경 문제)
   - **개선 방안**: MongoDB 또는 Redis로 마이그레이션 고려

#### Import 구조 문제점

1. **일관성 없는 DB 접근 패턴**
   - `characters.py`: Repository 패턴 사용 ✅
   - `games.py`, `game_turn.py`: MongoDB 직접 접근 ❌
   - **개선 방안**: Repository 패턴으로 통일

2. **의존성 방향 위반 (Clean Architecture)**
   - `routes` → `adapters/persistence/mongo` 직접 import
   - 원칙적으로는 `routes` → `factory` → `repository` → `adapter` 순서여야 함
   - **현재 상태**: 부분적으로만 Clean Architecture 준수

3. **환경변수 의존성**
   - MongoDB URI, DB 이름 등이 여러 곳에서 하드코딩되어 있음
   - **개선 방안**: 설정 관리 중앙화 (현재 `config.py` 있으나 완전하지 않음)

#### 결합도 요약

| 계층 | 의존 대상 | 위험도 | 비고 |
|------|-----------|--------|------|
| `routes` → `mongo` 직접 | 높음 | Repository 패턴 우회 |
| `routes` → `services` | 낮음 | 정상적인 의존성 |
| `services` → `mongo` | 중간 | 간접적 접근, 일부 직접 접근 |
| 메모리 세션 저장 | 높음 | 프로덕션 환경 문제 |
| 로컬 파일 세션 저장 | 높음 | 프로덕션 환경 문제 |

