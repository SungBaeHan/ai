# 디렉토리 구조

This document is reference/supplementary material. For canonical rules, see docs/SSOT.md and docs/ARCHITECTURE.md.

생성일: 2025-01-27

## 루트 디렉토리

```
.
├── .chat_history.json
├── .env.example
├── .gitignore
├── Dockerfile
├── GoogleClientSecret.json
├── infra_fix_qdrant.sh
├── render.yaml
├── requirements.txt
├── str
├── structure.txt
├── trpg-gen.Modelfile
├── trpg-polish.Modelfile
│
├── .vscode/
│   └── setting.json
│
├── adapters/
│   ├── __init__.py
│   ├── external/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── embedding/
│   │   │   ├── __init__.py
│   │   │   ├── sentence_transformer.py
│   │   │   └── sentence_transformer_adapter.py
│   │   └── openai/
│   │       ├── __init__.py
│   │       └── openai_client.py
│   ├── file_storage/
│   │   └── r2_storage.py
│   └── persistence/
│       ├── __init__.py
│       ├── factory.py
│       ├── mongo/
│       │   ├── __init__.py
│       │   ├── character_repository_adapter.py
│       │   └── factory.py
│       └── sqlite/
│           ├── __init__.py
│           ├── character_repository.py
│           └── character_repository_adapter.py
│
├── apps/
│   ├── api/
│   │   ├── bootstrap.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── startup.py
│   │   ├── utils.py
│   │   └── routes/
│   │       ├── app_api.py
│   │       ├── app_chat.py
│   │       ├── ask.py
│   │       ├── ask_chat.py
│   │       ├── assets.py
│   │       ├── auth.py
│   │       ├── auth_google.py
│   │       ├── characters.py
│   │       ├── chat.py
│   │       ├── debug.py
│   │       ├── debug_db.py
│   │       ├── health.py
│   │       └── migrate.py
│   ├── diag/
│   │   └── app.py
│   └── web-html/
│       ├── chat.html
│       ├── home.html
│       ├── index.html
│       ├── my.html
│       └── js/
│           └── config.js
│
├── assets/
│   ├── char/
│   │   └── [다수의 PNG 이미지 파일들]
│   ├── img/
│   │   ├── 7a6007f01e97.png
│   │   ├── char_01.jpg
│   │   ├── char_02.jpg
│   │   ├── char_03.jpg
│   │   ├── char_04.jpg
│   │   ├── char_05.jpg
│   │   ├── char_06.jpg
│   │   └── placeholder.jpg
│   ├── temp/
│   └── temp_back/
│       ├── 184c7182ca2db3d32352abe66d4c760c.jpg
│       ├── 4b0b8ae77eab79c0c6c61ba1d57bd3c1.jpg
│       ├── c5a5591d2e144a45c68973115d94f357.jpg
│       ├── ee224fa1ef2993ec2fa05228518964a9.jpg
│       └── f26b858e3576de95d622560792bc434e.jpg
│
├── data/
│   ├── app.sqlite3
│   ├── hello.txt
│   ├── db/
│   │   └── app.sqlite3
│   └── json/
│       ├── characters.json
│       └── home.json
│
├── docker/
│   ├── api.Dockerfile
│   ├── nginx.conf
│   └── nginx.Dockerfile
│
├── docker_img/
│   └── DockerDesktopWSL/
│       ├── disk/
│       │   └── docker_data.vhdx
│       └── main/
│           └── ext4.vhdx
│
├── docs/
│   ├── CURRENT_FILE_STRUCTURE.md
│   ├── deployment_history_2025-11-05.md
│   ├── deployment_history_2025-11-07.md
│   ├── deployment_history_2025-11-19.md
│   ├── deployment_history_2025-11-21.md
│   ├── deployment_history_2025-11-24.md
│   ├── deployment_history_2025-11-25.md
│   ├── DIRECTORY_STRUCTURE.md
│   ├── GOOGLE_LOGIN_SETUP.md
│   ├── QUICK_START.md
│   ├── README.md
│   ├── REFACTORING_SUMMARY.md
│   └── UNUSED_FEATURES.md
│
├── infra/
│   ├── .env
│   ├── .env .bak.20251117
│   ├── .env.bak.20251111-171956
│   ├── docker-compose.yml
│   ├── docker-compose.yml.bak.20251111-170033
│   ├── docker-compose.yml.bak.20251111-170057
│   ├── docker-entrypoint.sh
│   └── ollama-entrypoint.sh
│
├── packages/
│   ├── db/
│   │   └── __init__.py
│   └── rag/
│       ├── embedder.py
│       └── ingest.py
│
├── pem/
│   ├── ssh-key-2025-11-11.key
│   └── ssh-key-2025-11-11.key.pub
│
├── scripts/
│   ├── crawl_pinterest_download.py
│   ├── ensure_r2_env.sh
│   ├── generate_daily_report.py
│   ├── import_characters_from_json.py
│   ├── migrate_sqlite_to_mongo.py
│   ├── prepare_oracle_vm_compose.sh
│   ├── process_temp_images.py
│   ├── sync_env_files.sh
│   └── data/
│       ├── __init__.py
│       └── ingest_documents.py
│
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── character.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── character_repository.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── embedding_service.py
│   └── usecases/
│       ├── __init__.py
│       ├── character/
│       │   ├── __init__.py
│       │   ├── get_character.py
│       │   └── list_characters.py
│       └── rag/
│           ├── __init__.py
│           └── answer_question.py
│
├── tests/
│   └── test_cors.py
│
├── tmp/
│
├── _volumes/
│   ├── ollama_models/
│   │   ├── id_ed25519
│   │   ├── id_ed25519.pub
│   │   └── models/
│   │       └── blobs/
│   ├── qdrant/
│   └── qdrant_storage/
│       ├── .qdrant_fs_check
│       ├── raft_state.json
│       ├── aliases/
│       │   └── data.json
│       └── collections/
│
└── __pycache__/
```

## 주요 디렉토리 설명

### adapters/
외부 서비스 및 인프라스트럭처 어댑터
- `external/`: 외부 LLM 및 임베딩 서비스 클라이언트
- `file_storage/`: 파일 저장소 어댑터 (R2)
- `persistence/`: 데이터베이스 어댑터 (MongoDB, SQLite)

### apps/
애플리케이션 진입점
- `api/`: FastAPI 기반 REST API 서버
- `diag/`: 진단 도구
- `web-html/`: 정적 HTML 파일

### assets/
정적 자산 파일
- `char/`: 캐릭터 이미지 파일들
- `img/`: 일반 이미지 파일들
- `temp/`, `temp_back/`: 임시 파일 저장소

### data/
데이터 파일
- SQLite 데이터베이스 파일
- JSON 설정/데이터 파일

### docker/
Docker 관련 설정 파일

### docs/
프로젝트 문서

### infra/
인프라스트럭처 설정
- Docker Compose 설정
- 환경 변수 파일
- 엔트리포인트 스크립트

### packages/
공통 패키지
- `db/`: 데이터베이스 유틸리티
- `rag/`: RAG (Retrieval-Augmented Generation) 관련 코드

### scripts/
유틸리티 스크립트
- 데이터 마이그레이션
- 이미지 처리
- 환경 설정 등

### src/
소스 코드 (클린 아키텍처 구조)
- `domain/`: 도메인 모델
- `ports/`: 인터페이스 정의 (리포지토리, 서비스)
- `usecases/`: 유스케이스 구현

### tests/
테스트 코드

### _volumes/
Docker 볼륨 데이터
- Ollama 모델 저장소
- Qdrant 벡터 데이터베이스 저장소






















