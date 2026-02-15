#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/app/backend"
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
require_cmd curl
require_cmd lsof

kill_port 8000

if [[ -f "$ENV_FILE" ]]; then
  echo "Loading optional env overrides from: $ENV_FILE"
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

echo "Preparing backend venv + dependencies..."
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  (cd "$BACKEND_DIR" && python3 -m venv .venv)
fi
(cd "$BACKEND_DIR" && .venv/bin/pip install -r requirements.txt >/dev/null)

echo "Starting backend on :8000 (stub/offline)"
(
  cd "$BACKEND_DIR"
  exec env \
    PYTHONUNBUFFERED=1 \
    LLM_PROVIDER="stub" \
    LLM_OPENAI_API_KEY="" \
    LLM_OPENAI_API_KEY_FILE="" \
    .venv/bin/python -m app
) &
BACK_PID=$!

cleanup() {
  kill "$BACK_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for backend health..."
backend_ready="false"
for _i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    backend_ready="true"
    break
  fi
  sleep 0.5
done

if [[ "$backend_ready" != "true" ]]; then
  echo "Backend failed to become healthy on :8000." >&2
  echo "Try running the backend directly to see logs:" >&2
  echo "  cd \"$BACKEND_DIR\" && LLM_PROVIDER=stub .venv/bin/python -m app" >&2
  exit 1
fi

echo ""
echo "Running scenario runner..."
(
  cd "$BACKEND_DIR"
  .venv/bin/python scripts/scenario_runner_cli.py --base-url "http://localhost:8000"
)

echo ""
echo "Scenario runner complete."

