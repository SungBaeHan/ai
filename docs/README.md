# TRPG AI 프로젝트

TRPG 캐릭터와 대화하고 질문에 답변할 수 있는 AI 애플리케이션입니다.

## 아키텍처

이 프로젝트는 Clean Architecture 원칙을 따릅니다:

```
trpg-ai/
├── apps/              # 애플리케이션 레이어 (API, Web)
├── src/               # 도메인 및 비즈니스 로직
│   ├── domain/        # 도메인 엔티티
│   ├── usecases/      # 유즈케이스 (비즈니스 로직)
│   └── ports/         # 포트 (인터페이스)
├── adapters/          # 어댑터 (인프라 구현체)
└── scripts/           # 유틸리티 스크립트
```

## 사전 요구사항

### Docker 실행 방식
- Docker & Docker Compose
- 최소 8GB RAM (Ollama 모델 실행을 위해)

### 로컬 실행 방식
- Python 3.10+
- SQLite3
- Qdrant (벡터 DB)
- Ollama (LLM)

## 실행 방법

### 방법 1: Docker Compose로 실행 (권장)

#### 1단계: 환경 변수 설정 (선택사항)
```bash
# 프로젝트 루트에 .env 파일 생성 (선택사항)
OLLAMA_MODEL=trpg-gen
OLLAMA_POLISH_MODEL=trpg-polish
QDRANT_URL=http://localhost:6333
COLLECTION=my_docs
```

#### 2단계: Docker Compose 실행
```bash
# 프로젝트 루트에서 실행
cd infra
docker-compose up -d

# 또는 루트에서
docker-compose -f infra/docker-compose.yml up -d
```

#### 3단계: Ollama 모델 다운로드
```bash
# Ollama 컨테이너 접속
docker exec -it ollama ollama pull trpg-gen
docker exec -it ollama ollama pull trpg-polish
```

#### 4단계: 서비스 확인
- API 서버: http://localhost:8000
- Web UI: http://localhost:8080
- Qdrant 관리: http://localhost:6333/dashboard
- Ollama API: http://localhost:11434

#### 5단계: 서비스 중지
```bash
cd infra
docker-compose down

# 볼륨까지 삭제하려면
docker-compose down -v
```

### 방법 2: 로컬 실행

#### 1단계: 의존성 설치
```bash
pip install -r requirements.txt
```

#### 2단계: Qdrant 실행
```bash
# Docker로 Qdrant만 실행
docker run -d -p 6333:6333 -p 6334:6334 -v $(pwd)/_volumes/qdrant_storage:/qdrant/storage qdrant/qdrant

# 또는 로컬 Qdrant 설치 후
qdrant
```

#### 3단계: Ollama 실행
```bash
# Docker로 Ollama만 실행
docker run -d -p 11434:11434 -v $(pwd)/_volumes/ollama_models:/root/.ollama ollama/ollama

# 또는 로컬 Ollama 설치 후
ollama serve
```

#### 4단계: Ollama 모델 다운로드
```bash
ollama pull trpg-gen
ollama pull trpg-polish
```

#### 5단계: 환경 변수 설정
```bash
export OLLAMA_HOST=http://localhost:11434
export QDRANT_URL=http://localhost:6333
export COLLECTION=my_docs
export DB_PATH=./data/app.sqlite3
```

#### 6단계: 데이터베이스 초기화
```bash
python -c "from adapters.persistence.sqlite import init_db; init_db()"
```

#### 7단계: API 서버 실행
```bash
# 프로젝트 루트에서
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 8단계: 웹 서버 실행 (선택사항)
```bash
# Nginx 또는 다른 정적 파일 서버 사용
# 또는 Python으로 간단하게:
cd apps/web-html
python -m http.server 8080
```

## API 엔드포인트

### 캐릭터 API
- `GET /v1/characters` - 캐릭터 목록
- `GET /v1/characters/{id}` - 캐릭터 상세
- `GET /v1/characters/count` - 캐릭터 개수
- `POST /v1/characters` - 캐릭터 생성

### 채팅 API
- `POST /v1/chat/` - TRPG 채팅
- `POST /v1/chat/reset` - 세션 리셋

### 질의응답 API
- `GET /v1/ask?q={질문}` - RAG 기반 질문 응답
- `GET /v1/ask/health` - 건강 상태 확인

### 헬스 체크
- `GET /health` - 전체 서비스 건강 상태

### OpenAI 테스트
- `POST /api/test-openai-chat` - OpenAI API 연동 확인용 테스트 엔드포인트

## 문서 수집 및 인덱싱

RAG 기능을 사용하려면 문서를 Qdrant에 인덱싱해야 합니다:

```bash
# 문서 인덱싱
python scripts/data/ingest_documents.py /path/to/documents

# 환경 변수 설정 (선택사항)
export QDRANT_URL=http://localhost:6333
export COLLECTION=my_docs
```

## 캐릭터 데이터 임포트

```bash
# JSON에서 캐릭터 임포트
python scripts/import_characters_from_json.py

# JSON 파일 위치:
# - apps/web-html/json/characters.json
# - data/json/characters.json
```

## OpenAI API 연동 테스트

### 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정해야 합니다:

```bash
OPEN_API_KEY=sk-...  # OpenAI API 키
OPENAI_MODEL=gpt-4.1-mini  # 사용할 모델명 (기본값: gpt-4.1-mini)
OPENAI_API_BASE=https://api.openai.com/v1  # API 베이스 URL (기본값: https://api.openai.com/v1)
LLM_PROVIDER=openai  # LLM 제공자 선택 (openai 또는 ollama, 기본값: openai)
```

### 테스트 엔드포인트 호출

로컬 개발 환경에서:

```bash
curl -X POST "http://localhost:8000/api/test-openai-chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕, 릴리"}'
```

Docker / Oracle VM 환경에서:

1. `.env` 파일에 `OPEN_API_KEY`, `OPENAI_MODEL`, `OPENAI_API_BASE`가 설정되어 있어야 합니다.
2. Docker 컨테이너를 빌드하고 실행:
   ```bash
   docker compose build && docker compose up -d
   ```
3. VM 쉘에서 curl로 엔드포인트 호출:
   ```bash
   curl -X POST "http://localhost:8000/api/test-openai-chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "안녕, 릴리"}'
   ```

### LLM Provider 선택

환경 변수 `LLM_PROVIDER`를 통해 OpenAI와 Ollama를 선택적으로 사용할 수 있습니다:

- `LLM_PROVIDER=openai`: OpenAI API 사용 (기본값)
- `LLM_PROVIDER=ollama`: Ollama 로컬 모델 사용

기존 LLM 호출 코드는 자동으로 설정된 provider를 사용합니다.

## 문제 해결

### Ollama 모델이 로드되지 않는 경우
```bash
# 컨테이너에서 모델 확인
docker exec -it ollama ollama list

# 모델 다시 다운로드
docker exec -it ollama ollama pull trpg-gen
```

### Qdrant 연결 오류
```bash
# Qdrant 상태 확인
curl http://localhost:6333/health

# 컨테이너 로그 확인
docker logs qdrant
```

### API 서버 오류
```bash
# 로그 확인
docker logs trpg-api

# 컨테이너 재시작
docker-compose -f infra/docker-compose.yml restart api
```

### 포트 충돌
```yaml
# infra/docker-compose.yml에서 포트 변경
ports:
  - "8001:8000"  # API 포트 변경
  - "8081:80"    # Web 포트 변경
```

## 개발 환경 설정

### 코드 스타일
```bash
# (선택사항) Black, isort 등 사용
black .
isort .
```

### 테스트 실행
```bash
# (향후 추가 예정)
pytest tests/
```

## 프로젝트 구조 상세

### Domain Layer (`src/domain/`)
- 도메인 엔티티 정의 (Character 등)

### Use Cases Layer (`src/usecases/`)
- 비즈니스 로직 (GetCharacter, ListCharacters, AnswerQuestion 등)

### Ports Layer (`src/ports/`)
- 인터페이스 정의 (Repository, Service 등)

### Adapters Layer (`adapters/`)
- 인프라 구현체 (SQLite, SentenceTransformer 등)

## 라이선스

(라이선스 정보 추가)
