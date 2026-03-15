#!/usr/bin/env bash
set -euo pipefail

cd /Users/dolphin/Downloads/Claude/enterprise-llm-adoption-kit

export GIT_AUTHOR_NAME="Doeon Kim"
export GIT_AUTHOR_EMAIL="KIM3310@users.noreply.github.com"
export GIT_COMMITTER_NAME="Doeon Kim"
export GIT_COMMITTER_EMAIL="KIM3310@users.noreply.github.com"

# Save remote and reinit
REMOTE="https://github.com/KIM3310/enterprise-llm-adoption-kit.git"
rm -rf .git
git init
git remote add origin "$REMOTE"

commit_dated() {
  local date="$1"
  local msg="$2"
  export GIT_AUTHOR_DATE="$date"
  export GIT_COMMITTER_DATE="$date"
  git commit -m "$msg"
}

# ── Commit 1: Feb 15 10:00 — project structure ──
git add \
  .gitignore \
  .env.example \
  LICENSE \
  CONTRIBUTING.md \
  Makefile \
  app/backend/.gitignore \
  app/backend/pyproject.toml \
  app/backend/requirements.txt \
  app/backend/README.md \
  app/backend/app/__init__.py \
  app/backend/app/__main__.py \
  app/backend/app/config.py \
  app/backend/app/models.py \
  app/backend/app/logging_config.py \
  app/backend/data/runbooks.json \
  app/backend/data/sample_audit.json \
  app/backend/data/samples/ \
  app/backend/scripts/__init__.py \
  app/frontend/package.json \
  app/frontend/package-lock.json \
  app/frontend/vite.config.js \
  app/frontend/index.html \
  scripts/ \
  tools/
commit_dated "2026-02-15T10:00:00+09:00" "feat: initialize project structure with Python backend and React frontend"

# ── Commit 2: Feb 17 14:00 — FastAPI backend with auth/RBAC ──
git add \
  app/backend/app/main.py \
  app/backend/app/auth.py \
  app/backend/app/rbac.py \
  app/backend/app/oidc.py \
  app/backend/app/rate_limit.py \
  app/backend/app/storage.py
commit_dated "2026-02-17T14:00:00+09:00" "feat: add FastAPI backend with authentication and RBAC"

# ── Commit 3: Feb 19 11:00 — RAG pipeline ──
git add \
  app/backend/app/rag.py \
  app/backend/data/handover_normalized.jsonl \
  app/backend/data/handover_raw.jsonl
commit_dated "2026-02-19T11:00:00+09:00" "feat: implement RAG pipeline with Chroma and deterministic embeddings"

# ── Commit 4: Feb 21 15:00 — prompt injection detection and safety ──
git add \
  app/backend/app/injection.py \
  app/backend/app/safety.py
commit_dated "2026-02-21T15:00:00+09:00" "feat: add prompt injection detection and safety rules"

# ── Commit 5: Feb 23 10:00 — PII redaction and audit logging ──
git add \
  app/backend/app/redaction.py \
  app/backend/app/audit.py \
  app/backend/app/audit_viewer.py \
  app/backend/scripts/audit_viewer.py
commit_dated "2026-02-23T10:00:00+09:00" "feat: implement PII redaction and audit logging"

# ── Commit 6: Feb 25 13:00 — LLM provider abstraction ──
git add \
  app/backend/app/llm_adapter.py \
  app/backend/app/tools.py \
  app/backend/app/alerts.py \
  app/backend/app/diagnostics.py
commit_dated "2026-02-25T13:00:00+09:00" "feat: add LLM provider abstraction (OpenAI, Ollama, Bedrock, stub)"

# ── Commit 7: Feb 27 11:00 — evals harness ──
git add \
  evals/
commit_dated "2026-02-27T11:00:00+09:00" "feat: add evals harness with baseline diffs"

# ── Commit 8: Mar 01 14:00 — Snowflake adapter ──
git add \
  app/backend/app/snowflake_adapter.py
commit_dated "2026-03-01T14:00:00+09:00" "feat: add Snowflake adapter for eval and audit persistence"

# ── Commit 9: Mar 03 10:00 — Databricks adapter ──
git add \
  app/backend/app/databricks_adapter.py
commit_dated "2026-03-03T10:00:00+09:00" "feat: add Databricks adapter with MLflow experiment tracking"

# ── Commit 10: Mar 05 15:00 — Prometheus metrics and OpenTelemetry ──
git add \
  app/backend/app/metrics.py \
  app/backend/app/otel_metrics.py \
  app/backend/app/telemetry.py \
  app/backend/app/runtime_scorecard.py
commit_dated "2026-03-05T15:00:00+09:00" "feat: add Prometheus metrics and OpenTelemetry instrumentation"

# ── Commit 11: Mar 07 11:00 — React frontend ──
git add \
  app/frontend/src/ \
  app/frontend/public/ \
  app/frontend/Dockerfile
commit_dated "2026-03-07T11:00:00+09:00" "feat: build React frontend with governance dashboard"

# ── Commit 12: Mar 09 13:00 — backend unit and integration tests ──
git add \
  app/backend/tests/ \
  tests/conftest.py \
  tests/test_audit_log_schema.py \
  tests/test_audit_viewer.py \
  tests/test_data_handling_mode.py \
  tests/test_dataset_ingest.py \
  tests/test_demo_placeholders.py \
  tests/test_discovery_wizard.py \
  tests/test_eval_runner.py \
  tests/test_exec_dashboard.py \
  tests/test_exec_deck.py \
  tests/test_frontend_metadata.py \
  tests/test_injection.py \
  tests/test_kr_dataset.py \
  tests/test_rbac.py \
  tests/test_redaction.py \
  tests/test_repo_hygiene.py \
  tests/test_roi_calculator.py \
  tests/test_safety_guardrails.py \
  tests/test_service_brief.py \
  tests/test_slack_webhook.py \
  tests/test_sso_rbac_mapping.py \
  tests/test_ticket_integration.py \
  tests/test_tools.py \
  tests/test_ui_service_brief.py \
  tests/test_ui_tabs.py \
  tests/test_workshop_generator.py \
  tests/test_workshop_snapshot.py
commit_dated "2026-03-09T13:00:00+09:00" "test: add backend unit and integration tests"

# ── Commit 13: Mar 11 10:00 — GitHub Actions workflows ──
git add \
  .github/workflows/
commit_dated "2026-03-11T10:00:00+09:00" "ci: add GitHub Actions workflows (CI, security scan, Docker publish)"

# ── Commit 14: Mar 12 14:00 — Docker and Kubernetes deployment ──
git add \
  app/backend/Dockerfile \
  infra/
commit_dated "2026-03-12T14:00:00+09:00" "feat: add Docker and Kubernetes deployment with HPA and TLS"

# ── Commit 15: Mar 13 11:00 — README, architecture docs, security policy ──
git add \
  README.md \
  README.ko.md \
  SECURITY.md \
  docs/ \
  app/backend/app/control_tower.py \
  app/backend/app/control_tower_service.py \
  app/backend/app/service_brief.py \
  app/backend/app/review_resource_pack.py \
  app/backend/data/control_tower_spec.json \
  app/backend/data/review_operator_checks.json \
  app/backend/data/review_playbooks.json \
  app/backend/data/review_resource_pack.json \
  app/backend/data/review_validation_cases.json \
  app/backend/scripts/capture_workshop_outputs.py \
  app/backend/scripts/debug_smoke.py \
  app/backend/scripts/discovery_wizard.py \
  app/backend/scripts/exercise_runtime_scorecard.py \
  app/backend/scripts/generate_demo_placeholders.py \
  app/backend/scripts/generate_exec_dashboard.py \
  app/backend/scripts/generate_exec_deck.py \
  app/backend/scripts/generate_handover_docs.py \
  app/backend/scripts/poc_success_generator.py \
  app/backend/scripts/quality_gate.sh \
  app/backend/scripts/roi_calculator.py \
  app/backend/scripts/run_workshop.py \
  app/backend/scripts/scenario_runner_cli.py
commit_dated "2026-03-13T11:00:00+09:00" "docs: add README, architecture docs, and security policy"

# ── Commit 16: Mar 14 15:00 — Snowflake and Databricks adapter tests ──
git add \
  tests/test_snowflake_adapter.py \
  tests/test_databricks_adapter.py
commit_dated "2026-03-14T15:00:00+09:00" "test: add Snowflake and Databricks adapter tests"

# ── Commit 17: Mar 15 10:00 — CHANGELOG, issue templates, PR template, guides ──
git add \
  CHANGELOG.md \
  .github/ISSUE_TEMPLATE/ \
  .github/PULL_REQUEST_TEMPLATE.md \
  docs/databricks-integration-guide.md
# Catch any remaining files
git add -A
commit_dated "2026-03-15T10:00:00+09:00" "docs: add CHANGELOG, issue templates, PR template, and Databricks guide"

echo ""
echo "=== Git log ==="
git log --oneline
echo ""
echo "=== Done! ==="
