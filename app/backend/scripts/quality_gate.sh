#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python executable not found: ${PYTHON_BIN}" >&2
  exit 1
fi

echo "[1/4] syntax check (compileall)"
"${PYTHON_BIN}" -m compileall app scripts tests

echo "[2/4] dependency check (pip check)"
"${PYTHON_BIN}" -m pip check

echo "[3/4] unit/integration tests (pytest)"
"${PYTHON_BIN}" -m pytest -q

echo "[4/4] smoke diagnostics"
export SQLITE_PATH="${QUALITY_SQLITE_PATH:-/tmp/ellm_backend_quality.db}"
export AUDIT_LOG_PATH="${QUALITY_AUDIT_LOG_PATH:-/tmp/ellm_backend_quality_audit.log}"
export CHROMA_PERSIST_DIR="${QUALITY_CHROMA_DIR:-/tmp/ellm_backend_quality_chroma}"
"${PYTHON_BIN}" scripts/debug_smoke.py >/tmp/ellm_backend_quality_smoke.json
head -n 20 /tmp/ellm_backend_quality_smoke.json

echo "QUALITY GATE PASSED"
