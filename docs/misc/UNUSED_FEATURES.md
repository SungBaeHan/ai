# 사용하지 않는 기능 목록

## API 엔드포인트

다음 API 엔드포인트는 `home.html`과 `chat.html`에서 호출되지 않습니다:

### 1. `/v1/characters/count` (GET)
- **위치**: `apps/api/routes/characters.py`
- **용도**: 등록된 캐릭터 총 개수 반환
- **상태**: 프론트엔드에서 호출하지 않음
- **권장사항**: 필요시 삭제하거나, 관리자 페이지에서 사용할 수 있도록 유지

### 2. `/v1/characters` (POST)
- **위치**: `apps/api/routes/characters.py`
- **용도**: 캐릭터 생성
- **상태**: 프론트엔드에서 호출하지 않음
- **권장사항**: 관리자 도구나 스크립트에서 사용할 수 있으므로 유지 권장

### 3. `/v1/ask` (GET)
- **위치**: `apps/api/routes/ask.py`
- **용도**: RAG 기반 질문 응답
- **상태**: 프론트엔드에서 호출하지 않음 (`/v1/chat`만 사용)
- **권장사항**: RAG 기능이 별도로 필요할 수 있으므로 유지 권장

## 스크립트

모든 스크립트는 특정 용도로 사용 중입니다:
- `scripts/crawl_pinterest_download.py` - Pinterest 이미지 크롤링
- `scripts/import_characters_from_json.py` - JSON에서 캐릭터 임포트
- `scripts/process_temp_images.py` - 이미지 처리 및 메타데이터 생성
- `scripts/data/ingest_documents.py` - RAG를 위한 문서 인덱싱

## 실제로 사용되는 API 엔드포인트

### home.html에서 사용
- `GET /v1/characters?offset=0&limit=200` - 캐릭터 목록 조회

### chat.html에서 사용
- `GET /v1/characters/{id}` - 캐릭터 상세 조회
- `POST /v1/chat/` - TRPG 채팅 (LLM 호출)

### 기타
- `GET /` - 루트 경로 (API 정보)
- `GET /health` - 헬스 체크

## 참고사항

- 사용하지 않는 엔드포인트는 향후 관리자 도구나 API 확장 시 활용 가능
- `/v1/ask` 엔드포인트는 OpenAI 기반 RAG 기능으로 2025-11-21 업데이트됨 (참고: `deployment_history_2025-11-21.md`)


