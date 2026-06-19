#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/app/backend"
FRONTEND_DIR="$ROOT_DIR/app/frontend"
ENV_FILE="$HOME/.enterprise_llm_demo_env"
OLLAMA_HELPERS="$ROOT_DIR/scripts/ollama_helpers.sh"

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

DEMO_LLM_PROVIDER="${DEMO_LLM_PROVIDER:-auto}"
case "$DEMO_LLM_PROVIDER" in
  auto|stub|openai|openai_compatible|ollama)
    ;;
  *)
    echo "Invalid DEMO_LLM_PROVIDER: $DEMO_LLM_PROVIDER (expected: auto|stub|ollama|openai|openai_compatible)" >&2
    exit 1
    ;;
esac

SELECTED_PROVIDER="$DEMO_LLM_PROVIDER"
if [[ "$DEMO_LLM_PROVIDER" == "auto" ]]; then
  if command -v ollama >/dev/null 2>&1 && [[ -f "$OLLAMA_HELPERS" ]]; then
    # shellcheck disable=SC1090
    source "$OLLAMA_HELPERS"
    echo "Auto-detected Ollama CLI. Trying Ollama first."
    if ensure_ollama_ready; then
      SELECTED_PROVIDER="ollama"
    else
      echo "Ollama preflight failed; falling back to stub provider." >&2
      SELECTED_PROVIDER="stub"
    fi
  else
    SELECTED_PROVIDER="stub"
  fi
fi

if [[ "$SELECTED_PROVIDER" == "ollama" ]]; then
  if [[ ! -f "$OLLAMA_HELPERS" ]]; then
    echo "Missing Ollama helper file: $OLLAMA_HELPERS" >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  source "$OLLAMA_HELPERS"
  ensure_ollama_ready
  echo "Ollama ready: base_url=$(ollama_base_url) model=$(ollama_model_name)"
fi

if [[ "$SELECTED_PROVIDER" == "openai" || "$SELECTED_PROVIDER" == "openai_compatible" ]]; then
  if [[ -z "${LLM_OPENAI_API_KEY:-}" && -z "${LLM_OPENAI_API_KEY_FILE:-}" ]]; then
    echo "Warning: OpenAI key is not set; provider errors may fallback to stub." >&2
  fi
fi

echo "Using LLM provider: $SELECTED_PROVIDER"

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
if [[ "$SELECTED_PROVIDER" == "stub" ]]; then
  (
    cd "$BACKEND_DIR"
    exec env \
      PYTHONUNBUFFERED=1 \
      LLM_PROVIDER="stub" \
      LLM_OPENAI_API_KEY="" \
      LLM_OPENAI_API_KEY_FILE="" \
      .venv/bin/python -m app
  ) &
elif [[ "$SELECTED_PROVIDER" == "ollama" ]]; then
  (
    cd "$BACKEND_DIR"
    exec env \
      PYTHONUNBUFFERED=1 \
      LLM_PROVIDER="ollama" \
      LLM_MODEL="${DEMO_OLLAMA_MODEL:-$(ollama_model_name)}" \
      LLM_OLLAMA_BASE_URL="${DEMO_OLLAMA_BASE_URL:-$(ollama_base_url)}" \
      LLM_OPENAI_API_KEY="" \
      LLM_OPENAI_API_KEY_FILE="" \
      .venv/bin/python -m app
  ) &
else
  (
    cd "$BACKEND_DIR"
    exec env \
      PYTHONUNBUFFERED=1 \
      LLM_PROVIDER="$SELECTED_PROVIDER" \
      .venv/bin/python -m app
  ) &
fi
BACK_PID=$!

echo "Waiting for backend health..."
backend_ready="false"
for _i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    echo "Backend ready."
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
echo "Use case tour (3-5 min):"
echo "1) Issue Ops/Admin token in Access Control"
echo "2) Run UC1/UC2 and check Audit/Runtime/Metrics"
echo "3) In another terminal, run 'make scenario-run' or 'make scenario-demo-local'"
echo ""

wait
