#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/app/backend"
FRONTEND_DIR="$ROOT_DIR/app/frontend"
ENV_FILE="$HOME/.enterprise_llm_demo_env"

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN || true)"
  if [[ -n "${pids}" ]]; then
    echo "Killing listeners on :${port} (${pids})"
    kill ${pids} || true
  fi
}

kill_port 8000
kill_port 5173

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  echo "Missing backend venv: $BACKEND_DIR/.venv"
  exit 1
fi

echo "Starting backend on :8000"
(
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  python3 -m app
) &
BACK_PID=$!

echo "Starting frontend on :5173"
(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONT_PID=$!

cleanup() {
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
