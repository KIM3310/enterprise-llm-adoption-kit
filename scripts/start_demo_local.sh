#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/app/backend"
FRONTEND_DIR="$ROOT_DIR/app/frontend"
ENV_FILE="$HOME/.enterprise_llm_demo_env"

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing command: $cmd" >&2; exit 1; }
}

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN || true)"
  if [[ -n "${pids}" ]]; then
    echo "Killing listeners on :${port} (${pids})"
    kill ${pids} || true
  fi
}

require_cmd python3
require_cmd npm
require_cmd curl
require_cmd lsof

kill_port 8000
kill_port 5173

if [[ -f "$ENV_FILE" ]]; then
  echo "Loading optional env overrides from: $ENV_FILE"
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

DEMO_LLM_PROVIDER="${DEMO_LLM_PROVIDER:-stub}"
if [[ "$DEMO_LLM_PROVIDER" != "stub" && "$DEMO_LLM_PROVIDER" != "openai" && "$DEMO_LLM_PROVIDER" != "openai_compatible" ]]; then
  echo "Invalid DEMO_LLM_PROVIDER: $DEMO_LLM_PROVIDER (expected: stub|openai|openai_compatible)" >&2
  exit 1
fi

echo "Preparing backend venv + dependencies..."
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  (cd "$BACKEND_DIR" && python3 -m venv .venv)
fi
(cd "$BACKEND_DIR" && .venv/bin/pip install -r requirements.txt >/dev/null)

echo "Preparing frontend dependencies..."
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  (cd "$FRONTEND_DIR" && npm install >/dev/null)
fi

echo "Starting backend on :8000"
(
  cd "$BACKEND_DIR"
  if [[ "$DEMO_LLM_PROVIDER" == "stub" ]]; then
    exec env \
      PYTHONUNBUFFERED=1 \
      LLM_PROVIDER="stub" \
      LLM_OPENAI_API_KEY="" \
      LLM_OPENAI_API_KEY_FILE="" \
      .venv/bin/python -m app
  else
    exec env \
      PYTHONUNBUFFERED=1 \
      LLM_PROVIDER="$DEMO_LLM_PROVIDER" \
      .venv/bin/python -m app
  fi
) &
BACK_PID=$!

echo "Waiting for backend health..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  sleep 0.5
done

echo "Starting frontend on :5173"
(
  cd "$FRONTEND_DIR"
  exec npm run dev
) &
FRONT_PID=$!

cleanup() {
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "Open: http://localhost:5173"
echo ""

wait
