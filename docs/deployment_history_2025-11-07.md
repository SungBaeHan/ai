# 배포 이력 - 2025-11-07

## 주요 작업 내용

### 1. MongoDB 어댑터 및 마이그레이션 시스템 구축

#### 생성된 파일
- `adapters/persistence/mongo/__init__.py` - MongoDB 연결 및 초기화
- `adapters/persistence/mongo/character_repository_adapter.py` - MongoDB CharacterRepository 구현 (지연 연결 패턴)
- `adapters/persistence/mongo/factory.py` - MongoDB Repository 팩토리
- `adapters/persistence/factory.py` - 환경변수 기반 Repository 팩토리
- `apps/api/routes/migrate.py` - SQLite → MongoDB 마이그레이션 라우트
- `scripts/migrate_sqlite_to_mongo.py` - 로컬 마이그레이션 스크립트

#### 주요 기능
- 지연 연결 패턴: MongoDB 클라이언트를 import 시점이 아닌 실제 사용 시점에 생성
- 마이그레이션 엔드포인트: `POST /_ops/migrate/sqlite-to-mongo?tables=characters&limit=5000`
- 환경변수 기반 백엔드 선택: `DATA_BACKEND=mongo` 설정

### 2. Cloudflare R2 스토리지 통합

#### 생성된 파일
- `adapters/file_storage/r2_storage.py` - R2 스토리지 어댑터
- `apps/api/routes/assets.py` - 이미지 목록 API 라우터

#### 주요 기능
- Presigned URL 생성: R2에서 이미지 key를 가져와 presigned URL 생성
- 이미지 목록 API: `GET /assets/images?prefix=char/&limit=60&signed=true`
- 환경변수 체크: 필수 환경변수 누락 시 RuntimeError 발생

#### 수정된 파일
- `requirements.txt` - `boto3>=1.35.0` 추가
- `apps/api/main.py` - assets 라우터 등록

### 3. HTML 페이지 개선

#### 수정된 파일
- `apps/web-html/home.html` - R2 이미지 갤러리 추가, 절대경로 API 호출
- `apps/web-html/chat.html` - R2 이미지 갤러리 추가, 절대경로 API 호출
- `apps/web-html/index.html` - config.js 로드 추가
- `apps/web-html/my.html` - config.js 로드 추가

#### 생성된 파일
- `apps/web-html/js/config.js` - API 기본 URL 설정 (`https://arcanaverse.onrender.com`)

#### 주요 기능
- 절대경로 API 호출: Cloudflare Pages → Render API 절대경로 사용
- 이미지 갤러리: R2에서 presigned URL로 이미지 표시
- 환경별 설정: `window.API_BASE_URL`로 배포 환경에 맞게 쉽게 변경 가능

### 4. 진단 및 디버깅 시스템

#### 생성된 파일
- `apps/api/routes/debug_db.py` - 데이터베이스 상태 확인 라우터
- `apps/api/routes/health.py` - 헬스체크 라우터 (개선)
- `apps/diag/app.py` - 폴백 진단 앱
- `infra/docker-entrypoint.sh` - Docker 엔트리포인트 스크립트

#### 주요 기능
- 데이터베이스 진단: `GET /_debug/db` - SQLite 상태 확인
- 헬스체크: 
  - `GET /health` - 기본 헬스체크
  - `GET /health/env` - 환경변수 존재 여부 확인
  - `GET /health/db` - 데이터베이스 연결 상태 확인
- 폴백 진단 앱: 메인 앱 부팅 실패 시 `/diag/ping`, `/diag/env` 엔드포인트 제공
- 엔트리포인트 스크립트: Python 모듈 임포트 검증, 실패 시 폴백 앱으로 전환

### 5. 성능 최적화 및 환경 설정

#### 생성된 파일
- `apps/api/bootstrap.py` - 부팅 시 환경변수 설정
- `apps/api/startup.py` - MongoDB 인덱스 초기화

#### 수정된 파일
- `requirements.txt` - CPU 전용 PyTorch 설정 추가
  - `--extra-index-url https://download.pytorch.org/whl/cpu` 추가
- `apps/api/main.py` - bootstrap import 추가, Mongo repository factory 사용

#### 주요 기능
- CPU 전용 PyTorch: CUDA 빌드 방지, Render free tier 최적화
- 환경변수 조기 설정:
  - `CUDA_VISIBLE_DEVICES=""` - GPU 비활성화
  - `TOKENIZERS_PARALLELISM=false` - 토크나이저 병렬 처리 비활성화
  - `TRANSFORMERS_NO_ADVISORY_WARNINGS=1` - 경고 메시지 비활성화
- MongoDB 인덱스 자동 생성: `id` 필드에 고유 인덱스 생성

### 6. Docker 및 배포 설정 개선

#### 수정된 파일
- `Dockerfile` (루트) - ENTRYPOINT 설정, 환경변수 추가
- `docker/api.Dockerfile` - infra entrypoint 스크립트 복사 및 설정

#### 주요 변경사항
- ENTRYPOINT 강제: `/entrypoint.sh` 사용
- 환경변수 최적화:
  - `TOKENIZERS_PARALLELISM=false`
  - `TRANSFORMERS_NO_ADVISORY_WARNINGS=1`
  - `CUDA_VISIBLE_DEVICES=`
  - `PLAYWRIGHT_BROWSERS_PATH=0`
- CRLF 문제 방지: Windows에서 커밋된 스크립트의 CRLF 제거
- 정적 파일 서빙: `apps/web-html/assets` 디렉토리를 `/assets`로 마운트

### 7. 정적 파일 서빙

#### 수정된 파일
- `apps/api/main.py` - `apps/web-html/assets` 디렉토리를 `/assets`로 마운트

#### 주요 기능
- 정적 파일 자동 마운트: 경로 존재 여부 확인 후 마운트
- 로그 출력: 마운트 성공/실패 시 정보/경고 메시지 출력

## 배포 정보

### Render
- Dockerfile: `Dockerfile` (루트) 또는 `docker/api.Dockerfile`
- Branch: `prd`
- Start Command: `/app/infra/docker-entrypoint.sh`
- Health Check Path: `/health`

### 환경변수 설정

#### 필수 환경변수
- `DATA_BACKEND=mongo` - MongoDB 백엔드 사용
- `MONGO_URI` - MongoDB 연결 URI
- `MONGO_DB=arcanaverse` - MongoDB 데이터베이스 이름

#### R2 스토리지 (선택)
- `R2_ENDPOINT` - Cloudflare R2 엔드포인트
- `R2_BUCKET` - R2 버킷 이름
- `R2_ACCESS_KEY_ID` - R2 액세스 키
- `R2_SECRET_ACCESS_KEY` - R2 시크릿 키

#### 기타
- `PORT` - Render가 자동으로 주입 (기본값: 10000)
- `PYTHONPATH=/app` - Python 경로 설정

## API 엔드포인트

### 헬스체크
- `GET /health` - 기본 헬스체크
- `GET /health/env` - 환경변수 확인
- `GET /health/db` - 데이터베이스 연결 상태

### 진단
- `GET /_debug/db` - SQLite 데이터베이스 상태 확인
- `GET /diag/ping` - 폴백 앱 상태 확인
- `GET /diag/env` - 폴백 앱 환경변수 확인

### 마이그레이션
- `POST /_ops/migrate/sqlite-to-mongo?tables=characters&limit=5000` - SQLite → MongoDB 마이그레이션

### Assets
- `GET /assets/images?prefix=char/&limit=60&signed=true` - R2 이미지 목록 (presigned URL 포함)

## 주요 커밋

1. `cef6fb9` - Add MongoDB adapter, factory, and migration route for SQLite to MongoDB migration
2. `aebf725` - feat: add static file serving for apps/web-html/assets
3. `0a96bc3` - fix: use Mongo repository factory instead of SQLite in main.py

## 테스트

### 로컬 마이그레이션 스크립트 실행
```bash
set MONGO_URI=mongodb+srv://<USER>:<PASS>@<cluster>.mongodb.net/
set MONGO_DB=arcanaverse
python scripts/migrate_sqlite_to_mongo.py --sqlite ".\data\db\app.sqlite3" --tables characters --limit 5000
```

### API 테스트
```bash
# 헬스체크
curl https://arcanaverse.onrender.com/health

# 데이터베이스 상태
curl https://arcanaverse.onrender.com/health/db

# 이미지 목록
curl https://arcanaverse.onrender.com/assets/images?prefix=char/&limit=10&signed=true
```

## 주의사항

1. **MongoDB 연결**: 지연 연결 패턴 사용으로 import 시점에 연결하지 않음
2. **CPU 전용 PyTorch**: CUDA 빌드 방지로 Render free tier에서 안정적 실행
3. **폴백 진단 앱**: 메인 앱 부팅 실패 시에도 컨테이너가 종료되지 않음
4. **환경변수**: `DATA_BACKEND=mongo` 설정 필수



