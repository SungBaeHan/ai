# 현재 파일 구조

This document is reference/supplementary material. For canonical rules, see docs/SSOT.md and docs/ARCHITECTURE.md.

## 프로젝트 전체 구조

```
trpg-ai/
├── apps/                          # 애플리케이션 레이어
│   ├── api/                       # FastAPI 애플리케이션
│   │   ├── main.py                # API 진입점
│   │   ├── middleware/            # 미들웨어 (비어있음)
│   │   ├── routes/                # API 라우터
│   │   │   ├── app_api.py
│   │   │   ├── app_chat.py
│   │   │   ├── ask.py             # 질문 답변 엔드포인트
│   │   │   ├── ask_chat.py
│   │   │   ├── auth.py            # 인증 라우터
│   │   │   ├── auth_google.py     # Google 로그인
│   │   │   ├── characters.py      # 캐릭터 관리 (새 구조)
│   │   │   └── chat.py            # 채팅 라우터
│   │   └── schemas/               # Pydantic 스키마 (비어있음)
│   └── web-html/                  # 정적 HTML 파일
│       ├── assets/
│       ├── chat.html
│       ├── home.html
│       ├── index.html
│       └── my.html
├── src/                            # 🆕 Clean Architecture Core
│   ├── domain/                     # 도메인 레이어
│   │   └── character.py           # Character 도메인 엔티티
│   ├── usecases/                   # 유즈케이스 레이어
│   │   ├── character/
│   │   │   ├── get_character.py   # 캐릭터 조회 유즈케이스
│   │   │   └── list_characters.py # 캐릭터 목록 조회 유즈케이스
│   │   ├── chat/                   # 채팅 유즈케이스 (비어있음)
│   │   └── rag/
│   │       └── answer_question.py # 질문 답변 유즈케이스
│   └── ports/                      # 포트 레이어 (인터페이스)
│       ├── repositories/
│       │   └── character_repository.py  # CharacterRepository 인터페이스
│       └── services/
│           └── embedding_service.py     # EmbeddingService 인터페이스
├── adapters/                       # 🆕 Infrastructure Adapters
│   ├── persistence/                # 영속성 어댑터
│   │   ├── sqlite/
│   │   │   ├── character_repository_adapter.py  # SQLite CharacterRepository 구현
│   │   │   ├── character_repository.py
│   │   │   └── migrations/         # 데이터베이스 마이그레이션
│   │   └── qdrant/                 # Qdrant 벡터 DB (비어있음)
│   ├── external/                   # 외부 서비스 어댑터
│   │   ├── embedding/
│   │   │   ├── sentence_transformer.py
│   │   │   └── sentence_transformer_adapter.py  # SentenceTransformer 어댑터
│   │   └── ollama/                 # Ollama 어댑터 (비어있음)
│   └── file_storage/               # 파일 저장소 (비어있음)
├── scripts/                        # 유틸리티 스크립트
│   ├── data/
│   │   └── ingest_documents.py     # 문서 수집 스크립트
│   ├── dev/                        # 개발 스크립트 (비어있음)
│   ├── images/                     # 이미지 처리 스크립트 (비어있음)
│   ├── crawl_pinterest_download.py
│   ├── generate_daily_report.py
│   ├── import_characters_from_json.py
│   └── process_temp_images.py
├── tests/                          # 테스트 코드
│   ├── fixtures/
│   ├── integration/
│   └── unit/
├── docs/                           # 문서
│   ├── CURRENT_FILE_STRUCTURE.md   # 현재 파일 (이 파일)
│   ├── deployment_history_2025-11-05.md
│   ├── GOOGLE_LOGIN_SETUP.md
│   ├── QUICK_START.md
│   ├── README.md
│   ├── REFACTORING_SUMMARY.md
│   └── UNUSED_FEATURES.md
├── infra/                          # 인프라 설정
│   └── docker-compose.yml
├── docker/                         # Docker 설정
│   ├── api.Dockerfile
│   ├── nginx.conf
│   └── nginx.Dockerfile
├── assets/                         # 정적 파일
│   ├── char/                       # 캐릭터 이미지
│   ├── img/                        # 일반 이미지
│   ├── temp/                       # 임시 파일
│   └── temp_back/                  # 백업 임시 파일
├── data/                           # 데이터 파일
│   ├── app.sqlite3                 # SQLite 데이터베이스
│   ├── db/
│   │   └── app.sqlite3
│   ├── hello.txt
│   └── json/                       # JSON 데이터 파일
├── shared/                         # 공유 유틸리티
│   └── utils/
├── packages/                       # ⚠️ 레거시 (호환성 유지용)
│   ├── db/
│   └── rag/
├── _volumes/                       # Docker 볼륨
│   ├── ollama_models/
│   ├── qdrant/
│   └── qdrant_storage/
├── requirements.txt                # Python 의존성
├── GoogleClientSecret.json         # Google OAuth 설정
├── trpg-gen.Modelfile              # Ollama 모델 설정
└── trpg-polish.Modelfile           # Ollama 모델 설정
```

## 주요 디렉토리 설명

### `apps/`
- **api/**: FastAPI 기반 REST API 애플리케이션
  - `main.py`: FastAPI 앱 진입점
  - `routes/`: API 엔드포인트 라우터들
- **web-html/**: 정적 HTML 파일들

### `src/` (Clean Architecture Core)
- **domain/**: 도메인 엔티티 (비즈니스 로직의 핵심)
- **usecases/**: 유즈케이스 (애플리케이션 비즈니스 로직)
- **ports/**: 포트 (인터페이스 정의)
  - `repositories/`: 저장소 인터페이스
  - `services/`: 서비스 인터페이스

### `adapters/` (Infrastructure)
- **persistence/**: 데이터 영속성 어댑터
  - `sqlite/`: SQLite 구현체
  - `qdrant/`: Qdrant 벡터 DB (예정)
- **external/**: 외부 서비스 어댑터
  - `embedding/`: 임베딩 서비스
  - `ollama/`: Ollama LLM 서비스 (예정)
- **file_storage/**: 파일 저장소 어댑터 (예정)

### `scripts/`
- 데이터 수집, 이미지 처리, 캐릭터 임포트 등의 유틸리티 스크립트

### `tests/`
- 단위 테스트, 통합 테스트, 픽스처

### `docs/`
- 프로젝트 문서들

### `infra/`, `docker/`
- Docker 및 인프라 설정 파일들

### `assets/`, `data/`
- 정적 파일 및 데이터 파일들

## 아키텍처 패턴

이 프로젝트는 **Clean Architecture** 패턴을 따릅니다:

1. **Domain Layer** (`src/domain/`): 비즈니스 엔티티
2. **Use Cases Layer** (`src/usecases/`): 애플리케이션 비즈니스 로직
3. **Ports Layer** (`src/ports/`): 인터페이스 정의
4. **Adapters Layer** (`adapters/`): 외부 시스템과의 통합 구현

## 참고사항

- `packages/` 디렉토리는 레거시 코드로, 호환성을 위해 남겨두었습니다.
- 일부 디렉토리(`middleware/`, `schemas/`, `ollama/`, `qdrant/` 등)는 비어있지만 향후 확장을 위해 준비되어 있습니다.






















