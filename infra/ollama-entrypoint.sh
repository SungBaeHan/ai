#!/bin/sh

# Ollama 서비스 시작
echo "[Ollama] Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
echo "[Ollama] Ollama serve started (PID: $OLLAMA_PID)"

# 서비스가 준비될 때까지 대기
echo "[Ollama] Waiting for Ollama service to be ready..."
sleep 15

# Base 모델 설치 (이미 존재하면 건너뛰기)
BASE_MODEL="qwen2.5:7b-instruct-q2_K"
echo "[Ollama] Checking base model: $BASE_MODEL..."
if ollama list | grep -q "^$BASE_MODEL "; then
  echo "[Ollama] Base model $BASE_MODEL already exists, skipping pull"
else
  echo "[Ollama] Pulling base model: $BASE_MODEL..."
  if ollama pull "$BASE_MODEL" 2>&1; then
    echo "[Ollama] Successfully pulled base model: $BASE_MODEL"
  else
    echo "[Ollama] Warning: Failed to pull base model"
  fi
fi

# 커스텀 모델 생성 (이미 존재하면 건너뛰기)
echo "[Ollama] Checking custom models..."
for model in trpg-gen trpg-polish; do
  echo "[Ollama] Checking if $model exists..."
  if ollama list | grep -q "^$model "; then
    echo "[Ollama] Model $model already exists, skipping creation"
  else
    echo "[Ollama] Creating $model from Modelfile..."
    if ollama create "$model" -f "/$model.Modelfile" 2>&1; then
      echo "[Ollama] Successfully created $model"
    else
      echo "[Ollama] Warning: Failed to create $model"
    fi
  fi
done

echo "[Ollama] Initialization complete. Service running."

# Ollama 서비스 프로세스 유지
wait $OLLAMA_PID

