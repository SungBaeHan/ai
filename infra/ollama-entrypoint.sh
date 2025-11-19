#!/bin/sh

# Ollama 서비스 시작
echo "[Ollama] Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
echo "[Ollama] Ollama serve started (PID: $OLLAMA_PID)"

# 서비스가 준비될 때까지 대기
echo "[Ollama] Waiting for Ollama service to be ready..."
sleep 15

# 모델 설치 시도
echo "[Ollama] Pulling Ollama models..."
for model in trpg-gen trpg-polish; do
  echo "[Ollama] Attempting to pull $model..."
  if ollama pull "$model" 2>&1; then
    echo "[Ollama] Successfully pulled $model"
  else
    echo "[Ollama] Warning: Failed to pull $model (may already exist or network issue)"
  fi
done

echo "[Ollama] Initialization complete. Service running."

# Ollama 서비스 프로세스 유지
wait $OLLAMA_PID

