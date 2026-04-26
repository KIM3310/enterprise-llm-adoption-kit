SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.PHONY: eval-gate demo demo-local demo-ollama-local scenario-run scenario-demo-local scenario-demo-ollama-local backend-install frontend-install frontend-build quality-check bundle-application quality-backend smoke-backend verify sanitize datadog-plan datadog-sync

COMPOSE := docker compose -f infra/docker-compose.yml
BACKEND_DIR := app/backend
FRONTEND_DIR := app/frontend
BOOTSTRAP_PYTHON ?= python3
BACKEND_VENV := $(BACKEND_DIR)/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python
BACKEND_UVICORN := $(BACKEND_VENV)/bin/uvicorn
BACKEND_STAMP := $(BACKEND_VENV)/.installed-dev
FRONTEND_STAMP := $(FRONTEND_DIR)/node_modules/.package-lock.json

eval-gate:
	python3 evals/runner/eval_gate.py

backend-install: $(BACKEND_STAMP)

$(BACKEND_STAMP): $(BACKEND_DIR)/pyproject.toml $(BACKEND_DIR)/requirements.txt
	@if [ ! -x "$(BACKEND_PYTHON)" ] || ! $(BACKEND_PYTHON) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then \
		rm -rf $(BACKEND_VENV); \
		$(BOOTSTRAP_PYTHON) -m venv $(BACKEND_VENV); \
	fi
	@if ! $(BACKEND_PYTHON) -m pip --version >/dev/null 2>&1; then \
		$(BACKEND_PYTHON) -m ensurepip --upgrade; \
	fi
	@cd $(BACKEND_DIR) && \
		.venv/bin/python -m pip install --upgrade pip && \
		.venv/bin/python -m pip install -e ".[dev]"
	@touch $(BACKEND_STAMP)

frontend-install: $(FRONTEND_STAMP)

$(FRONTEND_STAMP): $(FRONTEND_DIR)/package.json $(FRONTEND_DIR)/package-lock.json
	@cd $(FRONTEND_DIR) && npm install --no-audit

demo:
	@echo "[1/6] starting services..."
	@docker info >/dev/null 2>&1 || { echo "Docker not running. Start Docker Desktop."; exit 1; }
	@$(COMPOSE) up -d --build
	@echo "OK"
	@echo "[2/6] health check..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -fsS http://localhost:8000/health >/dev/null && echo "OK" && break; \
		echo "Waiting for backend..."; \
		sleep 1; \
	done
	@curl -fsS http://localhost:8000/health >/dev/null || { echo "Health check failed at /health"; exit 1; }
	@echo "OK"
	@echo "[3/6] demo steps (3-min)"
	@echo "- Login as Ops"
	@echo "- UC1 query: Summarize handover risks for payments prod"
	@echo "- UC2 log: ERROR Timeout while calling payments API"
	@echo "[4/6] metrics snapshot..."
	@curl -fsS http://localhost:8000/metrics | head -n 20
	@echo "OK"
	@echo "[5/6] eval runner..."
	@$(COMPOSE) run --rm tools python3 evals/runner/run_eval.py \
		--dataset evals/datasets/initial_20.jsonl \
		--base-url http://backend:8000
	@echo "OK"
	@echo "[6/6] tests..."
	@$(COMPOSE) run --rm tools python3 -m pytest -q
	@echo "DEMO OK"

demo-local:
	@bash scripts/start_demo_local.sh

demo-ollama-local:
	@bash scripts/start_demo_ollama_local.sh

scenario-run:
	@cd app/backend && .venv/bin/python scripts/scenario_runner_cli.py --base-url http://localhost:8000

scenario-demo-local:
	@bash scripts/run_scenario_local.sh

scenario-demo-ollama-local:
	@bash scripts/run_scenario_ollama_local.sh

frontend-build: frontend-install
	@cd $(FRONTEND_DIR) && npm run build

quality-check: backend-install
	@cd app/backend && ./scripts/quality_gate.sh
	@$(MAKE) frontend-build

smoke-backend: backend-install
	@cd $(BACKEND_DIR) && \
	PORT=8012; \
	LOG=/tmp/enterprise-llm-adoption-kit-smoke.log; \
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $$PORT >$$LOG 2>&1 & \
	pid=$$!; \
	trap 'kill $$pid >/dev/null 2>&1 || true' EXIT INT TERM; \
	for _ in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -fsS "http://127.0.0.1:$$PORT/health" >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 1; \
	done; \
	curl -fsS "http://127.0.0.1:$$PORT/health" >/dev/null; \
	curl -fsS "http://127.0.0.1:$$PORT/ops/service-brief" >/dev/null; \
	curl -fsS "http://127.0.0.1:$$PORT/ops/resource-pack" >/dev/null; \
	echo "smoke ok: http://127.0.0.1:$$PORT"

verify: quality-check smoke-backend

datadog-plan:
	@python3 scripts/datadog_assets.py plan

datadog-sync:
	@python3 scripts/datadog_assets.py sync

bundle-application:
	@bash scripts/package_application.sh

quality-backend:
	@cd app/backend && ./scripts/quality_gate.sh

sanitize:
	@./scripts/sanitize_repo.sh
