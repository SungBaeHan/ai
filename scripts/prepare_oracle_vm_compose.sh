#!/usr/bin/env bash

set -euo pipefail

# === settings ===
# 레포 루트에서 실행해도, infra/에서 실행해도 동작하도록 compose 경로 자동 탐색
CANDIDATES=("docker-compose.yml" "compose.yml" "infra/docker-compose.yml" "infra/compose.yml")
COMPOSE_FILE=""

for c in "${CANDIDATES[@]}"; do
  if [[ -f "$c" ]]; then
    COMPOSE_FILE="$c"
    break
  fi
done

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "❌ docker-compose.yml(또는 compose.yml)을 찾지 못했습니다. 레포 루트/infra/에서 다시 실행하거나 경로를 수정하세요."
  exit 1
fi

COMPOSE_DIR="$(dirname "$COMPOSE_FILE")"
REPO_ROOT="$(pwd)"

echo "▶️  compose 파일: $COMPOSE_FILE"
echo "▶️  작업 디렉토리: $COMPOSE_DIR"

# 백업
BACKUP="$COMPOSE_FILE.bak.$(date +%Y%m%d-%H%M%S)"
cp -a "$COMPOSE_FILE" "$BACKUP"
echo "💾 백업 생성: $BACKUP"

# docker-entrypoint.sh 실행권한 부여(있을 경우)
if [[ -f "$REPO_ROOT/docker-entrypoint.sh" ]]; then
  chmod +x "$REPO_ROOT/docker-entrypoint.sh"
  echo "🔧 실행권한 부여: ./docker-entrypoint.sh"
elif [[ -f "$COMPOSE_DIR/docker-entrypoint.sh" ]]; then
  chmod +x "$COMPOSE_DIR/docker-entrypoint.sh"
  echo "🔧 실행권한 부여: $COMPOSE_DIR/docker-entrypoint.sh"
else
  echo "ℹ️  docker-entrypoint.sh 파일을 찾지 못했지만, 계속 진행합니다. (entrypoint 경로는 아래에서 설정)"
fi

# ruamel.yaml 설치 (사용자 영역)
python3 - <<'PYSETUP'
import sys, subprocess
try:
    import ruamel.yaml  # type: ignore
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "ruamel.yaml"])
PYSETUP

# YAML 패치
python3 - "$COMPOSE_FILE" <<'PYPATCH'
import sys, os, copy
from pathlib import Path

compose_path = Path(sys.argv[1])

from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True

data = yaml.load(compose_path.read_text(encoding="utf-8"))
if not isinstance(data, dict) or "services" not in data:
    print("❌ services 키가 없는 compose 파일입니다.", file=sys.stderr)
    sys.exit(1)

services = data.get("services", {})

def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

# --- api 서비스 패치 ---
api = services.get("api")
if api is None:
    print("❌ services.api 를 찾지 못했습니다.", file=sys.stderr)
    sys.exit(1)

# env_file 추가(.env)
env_file = ensure_list(api.get("env_file"))
if ".env" not in env_file and "./.env" not in env_file:
    env_file.append(".env")
api["env_file"] = env_file

# entrypoint 설정 (docker-entrypoint.sh)
api["entrypoint"] = ["/app/docker-entrypoint.sh"]
# command 제거(엔트리포인트가 uvicorn 실행)
api.pop("command", None)

# environment에서 SQLite 경로(DB_PATH) 제거, OLLAMA_HOST(Windows 전용)는 제거/주석화
env = api.get("environment", {})
if isinstance(env, list):
    # 키-값 리스트로 된 경우도 있음 → dict로 치환
    env_dict = {}
    for item in env:
        if isinstance(item, str) and "=" in item:
            k, v = item.split("=", 1)
            env_dict[k.strip()] = v
    env = env_dict

for k in ["DB_PATH", "SQLITE_PATH"]:
    if k in env:
        env.pop(k)

# OLLAMA_HOST가 host.docker.internal 이면 제거 (VM에선 불필요/오동작)
if "OLLAMA_HOST" in env and "host.docker.internal" in str(env["OLLAMA_HOST"]):
    env.pop("OLLAMA_HOST")

api["environment"] = env

# volumes에서 ./data/db → /data/db 매핑 제거(SQLite 종료)
vols = ensure_list(api.get("volumes"))
new_vols = []
for v in vols:
    s = str(v)
    if ("/data/db" in s) or (s.endswith(": /data/db") or s.endswith(":/data/db")):
        continue
    new_vols.append(v)
api["volumes"] = new_vols

# ports: 8000:8000 보장
ports = ensure_list(api.get("ports"))
has_8000 = any(str(p).startswith("8000:") or str(p).endswith(":8000") or str(p)=="8000" for p in ports)
if not has_8000:
    ports.append("8000:8000")
api["ports"] = ports

# depends_on에 qdrant 유지(있으면), 없으면 건드리지 않음
# (Qdrant를 안 쓸 경우, 사용자가 직접 삭제할 수 있도록 자동 추가는 하지 않음)

services["api"] = api

# --- qdrant 서비스 패치(외부 노출 최소화: 127.0.0.1 바인딩 또는 제거) ---
qd = services.get("qdrant")
if qd:
    qports = []
    for p in ensure_list(qd.get("ports")):
        ps = str(p)
        # 6333 / 6334를 로컬호스트 바인딩으로 교체
        if ps.endswith(":6333") or ps == "6333":
            qports.append("127.0.0.1:6333:6333")
        elif ps.endswith(":6334") or ps == "6334":
            qports.append("127.0.0.1:6334:6334")
        else:
            # 그 외 포트는 유지
            qports.append(ps)
    # 중복 제거
    qports = list(dict.fromkeys(qports))
    if qports:
        qd["ports"] = qports
    services["qdrant"] = qd

# --- ollama 서비스 패치(있으면 OLLAMA_HOST 환경 제거—VM 친화) ---
ol = services.get("ollama")
if ol:
    env = ol.get("environment", {})
    if isinstance(env, list):
        env_dict = {}
        for item in env:
            if isinstance(item, str) and "=" in item:
                k, v = item.split("=", 1)
                env_dict[k.strip()] = v
        env = env_dict
    if "OLLAMA_HOST" in env and "host.docker.internal" in str(env["OLLAMA_HOST"]):
        env.pop("OLLAMA_HOST")
    ol["environment"] = env
    services["ollama"] = ol

data["services"] = services

compose_path.write_text("", encoding="utf-8")  # truncate
yaml.dump(data, compose_path.open("w", encoding="utf-8"))

print("✅ docker-compose.yml 패치 완료:", compose_path)
PYPATCH

# .env 템플릿 생성(없을 때만)
ENV_PATH="$COMPOSE_DIR/.env"
if [[ ! -f "$ENV_PATH" ]]; then
  cat > "$ENV_PATH" <<'ENVEOF'
# === Runtime ===
APP_ENV=prod
PORT=8000
APP_MODULE=apps.api.main:app
UVICORN_WORKERS=2

# === MongoDB(Atlas) ===
MONGO_URI=mongodb+srv://<USER>:<PASS>@<CLUSTER_HOST>/<DB_NAME>?retryWrites=true&w=majority
DB_NAME=arcanaverse

# === Optional: Qdrant 내부접속용 ===
# QDRANT_URL=http://qdrant:6333

# === OAuth/JWT ===
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
JWT_SECRET=Arcanaverse

# === CORS (쉼표로 구분) ===
CORS_ALLOW_ORIGINS=http://localhost:8080,https://arcanaverse.ai,https://www.arcanaverse.ai,https://api.arcanaverse.ai
ENVEOF
  chmod 600 "$ENV_PATH"
  echo "📝 .env 템플릿 생성: $ENV_PATH (값 채워넣으세요)"
else
  echo "ℹ️  .env가 이미 존재—생성 건너뜀: $ENV_PATH"
fi

# 변경 요약(diff)
echo
echo "=== 변경 요약 (diff) ==="
set +e
git --version >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
  # git이 있으면 컬러 diff
  git --no-pager diff --no-index "$BACKUP" "$COMPOSE_FILE" || true
else
  diff -u "$BACKUP" "$COMPOSE_FILE" || true
fi
set -e

echo
echo "🎉 완료!"
echo "다음 명령으로 빌드/기동하세요:"
echo "  cd \"$(dirname "$COMPOSE_FILE")\""
echo "  docker compose up -d --build"

