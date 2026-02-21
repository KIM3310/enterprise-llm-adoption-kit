#!/usr/bin/env bash
set -euo pipefail

ollama_base_url() {
  echo "${DEMO_OLLAMA_BASE_URL:-${OLLAMA_BASE_URL:-http://127.0.0.1:11434}}"
}

ollama_model_name() {
  echo "${DEMO_OLLAMA_MODEL:-${OLLAMA_MODEL:-llama3.2:latest}}"
}

ollama_health_url() {
  local base="${1:-$(ollama_base_url)}"
  base="${base%/}"
  echo "${base}/api/tags"
}

wait_for_ollama() {
  local health_url="$1"
  local attempts="${2:-30}"
  local sleep_sec="${3:-0.5}"
  local i
  for ((i = 0; i < attempts; i += 1)); do
    if curl -fsS --max-time 2 "${health_url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_sec}"
  done
  return 1
}

ensure_ollama_ready() {
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama CLI not found. Install: https://ollama.com/download" >&2
    return 1
  fi

  local base_url
  local health_url
  local model
  base_url="$(ollama_base_url)"
  health_url="$(ollama_health_url "${base_url}")"
  model="$(ollama_model_name)"

  if ! curl -fsS --max-time 2 "${health_url}" >/dev/null 2>&1; then
    if [[ "${DEMO_OLLAMA_AUTO_SERVE:-1}" == "1" ]]; then
      echo "Starting ollama server..."
      nohup ollama serve >/tmp/enterprise_llm_ollama.log 2>&1 &
    fi
  fi

  if ! wait_for_ollama "${health_url}" 40 0.5; then
    echo "Ollama server is not reachable at ${health_url}" >&2
    return 1
  fi

  if [[ "${DEMO_OLLAMA_AUTO_PULL:-1}" == "1" ]]; then
    if ! ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | grep -Fx "${model}" >/dev/null 2>&1; then
      echo "Pulling Ollama model: ${model}"
      ollama pull "${model}"
    fi
  fi

  export DEMO_OLLAMA_BASE_URL="${base_url}"
  export DEMO_OLLAMA_MODEL="${model}"
  return 0
}
