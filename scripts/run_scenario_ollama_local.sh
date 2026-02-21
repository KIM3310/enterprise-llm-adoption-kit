#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export DEMO_LLM_PROVIDER="ollama"

exec bash "$ROOT_DIR/scripts/run_scenario_local.sh"
