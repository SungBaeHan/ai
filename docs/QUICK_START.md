# 빠른 시작 가이드

## 🚀 Docker Compose로 빠르게 시작하기

### 1. 서비스 시작
```bash
cd infra
docker-compose up -d
```

### 2. Ollama 모델 다운로드
```bash
docker exec -it ollama ollama pull trpg-gen
docker exec -it ollama ollama pull trpg-polish
```

### 3. 접속 확인
- 🌐 웹 UI: http://localhost:8080
- 🔌 API: http://localhost:8000
- 📊 API 문서: http://localhost:8000/docs

### 4. 서비스 중지
```bash
cd infra
docker-compose down
```

## 📝 주요 명령어

// ... existing code ...

## 🔍 문제 해결

### nginx 403 Forbidden 오류
nginx 설정을 업데이트했으므로 웹 서버를 재빌드하세요:
```bash
# 웹 서버 재빌드
docker-compose -f infra/docker-compose.yml build web

# 웹 서버 재시작
docker-compose -f infra/docker-compose.yml up -d web
```

또는 전체 재빌드:
```bash
cd infra
docker-compose up -d --build
```

접속 URL:
- http://localhost:8080/ → home.html로 리다이렉트
- http://localhost:8080/home.html → 홈 페이지
- http://localhost:8080/chat.html → 채팅 페이지
- http://localhost:8080/v1/characters → API 자동 프록시

### 포트가 이미 사용 중인 경우
`infra/docker-compose.yml`에서 포트 변경:
```yaml
ports:
  - "8001:8000"  # API 포트 변경
  - "8081:80"    # Web 포트 변경
```

### 모델이 로드되지 않는 경우
```bash
# Ollama 컨테이너 재시작
docker-compose -f infra/docker-compose.yml restart ollama

# 모델 다시 다운로드
docker exec -it ollama ollama pull trpg-gen
```

### 컨테이너 로그 확인
```bash
# 모든 서비스 로그
docker-compose -f infra/docker-compose.yml logs

# 특정 서비스만
docker logs trpg-api
docker logs ollama
docker logs qdrant
docker logs trpg-web
```

## 📚 더 자세한 정보

전체 문서는 [README.md](README.md)를 참고하세요.
