#!/usr/bin/env bash
set -euo pipefail

ROOT_ENV=".env"
INFRA_ENV="infra/.env"

# 파일 존재 보장
touch "$ROOT_ENV" "$INFRA_ENV"

# 관리할 키들 배열
declare -a KEYS=(
  "R2_ENDPOINT"
  "R2_BUCKET"
  "R2_ACCESS_KEY_ID"
  "R2_SECRET_ACCESS_KEY"
)

# .env 파일에서 키의 값을 읽어오는 함수
get_env_value() {
  local key="$1"
  local file="$2"
  if [[ -f "$file" ]]; then
    grep -E "^${key}=" "$file" 2>/dev/null | cut -d'=' -f2- | sed 's/^"//;s/"$//' || echo ""
  else
    echo ""
  fi
}

# .env 파일에 키-값을 설정하는 함수 (있으면 덮어쓰고, 없으면 추가)
set_env_value() {
  local key="$1"
  local value="$2"
  local file="$3"
  
  # 임시 파일 생성
  local temp_file="${file}.tmp"
  
  # 키가 이미 존재하는지 확인
  if grep -qE "^${key}=" "$file" 2>/dev/null; then
    # 키가 있으면 해당 라인을 덮어쓰기
    sed "s|^${key}=.*|${key}=${value}|" "$file" > "$temp_file"
    mv "$temp_file" "$file"
  else
    # 키가 없으면 맨 끝에 추가
    echo "${key}=${value}" >> "$file"
  fi
}

# 처리 내역 추적
declare -a PROCESSED_KEYS=()

# 각 키에 대해 처리
for key in "${KEYS[@]}"; do
  # 1) .env에서 값 읽기
  root_value=$(get_env_value "$key" "$ROOT_ENV")
  
  # 2) .env에 값이 없으면 사용자에게 입력받기
  if [[ -z "$root_value" ]]; then
    read -rp "Enter ${key}: " root_value
    if [[ -z "$root_value" ]]; then
      echo "[WARN] ${key} is empty, skipping..."
      continue
    fi
    # .env에 저장
    set_env_value "$key" "$root_value" "$ROOT_ENV"
    echo "[INFO] Set ${key} in ${ROOT_ENV}"
  else
    echo "[INFO] Found ${key} in ${ROOT_ENV}, using existing value"
  fi
  
  # 3) infra/.env에는 항상 .env의 값으로 덮어쓰기
  current_root_value=$(get_env_value "$key" "$ROOT_ENV")
  if [[ -n "$current_root_value" ]]; then
    set_env_value "$key" "$current_root_value" "$INFRA_ENV"
    echo "[INFO] Synced ${key} to ${INFRA_ENV}"
    PROCESSED_KEYS+=("${key}")
  fi
done

# 요약 출력
echo ""
echo "=========================================="
echo "R2 환경변수 설정 요약"
echo "=========================================="
for key in "${PROCESSED_KEYS[@]}"; do
  root_val=$(get_env_value "$key" "$ROOT_ENV")
  infra_val=$(get_env_value "$key" "$INFRA_ENV")
  
  # 값의 일부만 표시 (보안)
  if [[ ${#root_val} -gt 20 ]]; then
    root_display="${root_val:0:20}..."
  else
    root_display="$root_val"
  fi
  
  echo "  ${key}:"
  echo "    .env:        ${root_display}"
  echo "    infra/.env: ${infra_val:0:20}..."
done
echo "=========================================="
echo ""

# 사용법 안내
echo "Done. R2 환경변수가 .env 와 infra/.env 에 동기화되었습니다."
echo ""
echo "다음 명령으로 컨테이너를 재시작하세요:"
echo "  cd infra && docker compose down && docker compose up -d"

