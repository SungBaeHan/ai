#!/usr/bin/env bash

set -euo pipefail

export PYTHONUNBUFFERED=1
export PYTHONPATH=${PYTHONPATH:-/app}
export APP_MODULE=${APP_MODULE:-apps.api.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-10000}

echo "==== STARTUP CHECK ===="
echo "PWD=$(pwd)"
echo "PYTHONPATH=$PYTHONPATH"
echo "APP_MODULE=$APP_MODULE"
echo "PORT=$PORT"
echo "LIST /app:"
ls -la /app || true

echo "---- Python import probe ----"
python - <<'PY'
import importlib, os, sys, traceback
mod = os.environ.get("APP_MODULE","apps.api.main:app").split(":")[0]
try:
    importlib.import_module(mod)
    print(f"[PROBE] OK import {mod}")
except Exception:
    print("[PROBE] IMPORT FAILED", mod)
    traceback.print_exc()
    sys.exit(42)
PY

probe_rc=$? || true

if [ "$probe_rc" != "0" ]; then
  echo "==== FALLBACK MODE (diag) ===="
  exec uvicorn apps.diag.app:app --host "$HOST" --port "$PORT" --log-level info
fi

echo "==== START MAIN APP ===="
exec uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --log-level info

