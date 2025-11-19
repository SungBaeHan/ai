#!/bin/sh

# Ollama 서비스 시작
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
echo "Ollama serve started (PID: $OLLAMA_PID)"

# 서비스가 준비될 때까지 대기 (curl이 없을 수 있으므로 간단한 대기)
echo "Waiting for Ollama service to be ready..."
sleep 10

# 모델 설치 시도 (최대 3회 재시도)
echo "Pulling Ollama models..."
for model in trpg-gen trpg-polish; do
  echo "Pulling $model..."
  retry=0
  while [ $retry -lt 3 ]; do
    if ollama pull "$model" 2>&1; then
      echo "Successfully pulled $model"
      break
    else
      retry=$((retry + 1))
      if [ $retry -lt 3 ]; then
        echo "Retrying $model pull... ($retry/3)"
        sleep 5
      else
        echo "Warning: Failed to pull $model after 3 attempts"
      fi
    fi
  done
done

echo "Ollama initialization complete."

# Ollama 서비스 프로세스 유지
wait $OLLAMA_PID

