# docker/api.Dockerfile
FROM python:3.12-slim

# 최소 빌드 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) requirements*.txt 중 존재하는 것만 복사 (최소 requirements.txt는 존재)
#    와일드카드는 최소 하나만 매칭돼도 성공하므로 안전합니다.
COPY requirements*.txt /app/

# 2) 설치: base가 있으면 우선, 없으면 requirements.txt,
#    둘 다 없으면 FastAPI 최소 셋 설치 (방어 로직)
RUN if [ -f requirements.base.txt ]; then \
      pip install --no-cache-dir -r requirements.base.txt ; \
    elif [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt ; \
    else \
      pip install --no-cache-dir fastapi uvicorn[standard] ; \
    fi

# 앱 코드/정적 리소스 반영
COPY apps /app/apps
COPY packages /app/packages
COPY adapters /app/adapters
COPY src /app/src
COPY data/json /app/data/json
COPY assets /app/assets

# SQLite 경로
RUN mkdir -p /data/db

# 실행 커맨드는 compose에서 지정
