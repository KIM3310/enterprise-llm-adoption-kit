.SHELLFLAGS := -eu -o pipefail -c
.PHONY: eval-gate demo demo-local demo-ollama-local scenario-run scenario-demo-local scenario-demo-ollama-local quality-backend sanitize

COMPOSE := docker compose -f infra/docker-compose.yml

eval-gate:
	python3 evals/runner/eval_gate.py

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

quality-backend:
	@cd app/backend && ./scripts/quality_gate.sh

sanitize:
	@./scripts/sanitize_repo.sh
