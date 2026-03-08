# Enterprise LLM Adoption Kit (Korea) - Portfolio
Tagline: Discovery -> Secure Architecture -> Evals -> Deployment/LLMOps
Note: This is a personal portfolio project. No real customers or production deployments are represented; all data and scenarios are synthetic or hypothetical.

Korean version: `README.ko.md`

## Demo video
- YouTube: https://youtu.be/yMq03b0js0E

## Snapshot
![Executive value dashboard snapshot](docs/sales/exec_value_dashboard/snapshot.svg)

## Project summary (entry-level, hands-on focus)
- Built an end-to-end adoption kit to show how enterprise LLM discovery turns into a secure, testable, and observable PoC.
- Implemented a working backend + frontend demo so reviewers can run it locally and verify behavior.
- Kept the scope realistic: stub LLM adapter, synthetic data, and explicit limitations so the portfolio stays honest.

## My role & scope
- Solo implementation of backend API, frontend UI, eval harness, and pre-sales artifacts.
- Focused on reproducibility: every claim is backed by a doc, a test, or a runnable script.
- Designed with "new hire readiness" in mind: clear separation of concerns, simple setup, and safe defaults.
- Added CI checks via GitHub Actions (backend quality gate, frontend build, eval gate).

## Core capabilities (what you can see working)
- Role-based access (RBAC) enforced at retrieval time
- Prompt injection detection + safety refusal rules
- PII redaction and audit logging with enterprise-mode hashing
- RAG-style retrieval (Chroma + deterministic hash embeddings)
- Evals with reports + baseline diffs
- LLMOps-ready metrics (latency, tokens, cost, policy events)
- Integration patterns: Slack/Jira-style ingestion endpoints (simulatable from the UI)
- Scenario Runner exports a shareable Markdown report and keeps a local run history (browser localStorage)
- Pre-sales artifacts: discovery wizard, ROI calculator, demo scripts, exec deck

## Architecture at a glance (local demo)
- FastAPI backend for UC1/UC2 flows, audit log, metrics, and integrations
- React (Vite) frontend for demo and review workflows
- Chroma for retrieval store (local persistence)
- SQLite for daily cost rollups

## Troubleshooting & verification notes (reproducible checks)
- RBAC leakage risk: access-group filtering enforced in retrieval and re-checked post-query. Verification: `tests/test_rbac.py` and AT-02 in `docs/blueprint/06_acceptance_tests.md`.
- Safety guardrails: refusal rules + prompt injection detection. Verification: `tests/test_safety_guardrails.py` and `tests/test_injection.py`.
- Audit data handling: enterprise mode hashes input/output instead of storing raw text. Verification: `tests/test_data_handling_mode.py`.
- RAG cold-start: index build on startup + normalized dataset generation when missing. Verification: run the demo and confirm citations appear for UC1.
- Python 3.14 compatibility: if `chromadb` import fails (pydantic-v1 issue), the app auto-falls back to a deterministic local retrieval backend so demo flows still run.
- LLM reliability: retry with exponential backoff on provider errors and metrics emitted at `/metrics`.

## What this demonstrates
- Enterprise discovery translated into architecture decisions
- LLM application integration patterns (RBAC, audit logging, redaction, injection defense, tool allowlist)
- Evals harness with regression + baseline diff
- LLMOps readiness (metrics, reliability controls, cost tracking)
- Pre-sales artifacts (demo scripts, objections, MAP, 30/60/90)
- LLM adoption paths (API vs LLM Workspace) and hybrid rollout planning

## Evidence (what to look at)
- RBAC proof: follow AT-02 in [docs/blueprint/06_acceptance_tests.md](docs/blueprint/06_acceptance_tests.md) (login as Employee vs Admin, run the same UC1 query, compare citations)
- Audit proof: [app/backend/data/sample_audit.json](app/backend/data/sample_audit.json)
- Eval proof: [evals/reports/latest_report.md](evals/reports/latest_report.md)
- Metrics proof: see [docs/blueprint/05_llmops_plan.md](docs/blueprint/05_llmops_plan.md) and `GET /metrics` (counters + latency histogram + policy events)
- Demo scripts: [docs/sales/demo_script_exec.md](docs/sales/demo_script_exec.md), [docs/sales/demo_script_eng.md](docs/sales/demo_script_eng.md)

Quick verify:
```bash
ls app/backend/data/sample_audit.json evals/reports/latest_report.md docs/sales/demo_script_exec.md docs/sales/demo_script_eng.md docs/blueprint/06_acceptance_tests.md
curl -fsS http://localhost:8000/metrics | head -n 20
curl -fsS http://localhost:8000/ops/service-brief | python3 -m json.tool | head -n 60
curl -fsS http://localhost:8000/ops/service-brief/schema | python3 -m json.tool | head -n 40
```

## Service-grade surfaces
- `GET /ops/service-brief`: concise runtime + evidence + rollout stage contract for buyers, operators, and reviewers
- `GET /ops/service-brief/schema`: explicit contract surface for the service brief payload
- Home/Readiness UI now renders an `Executive Readiness Board`, even in static mode, so the portfolio still reads like a service when the backend is offline
- See `SERVICE_GRADE_SPECKIT.ko.md` for the spec-first reasoning behind this iteration

## Customer journey (Discovery -> Production)
- Blueprint: `docs/blueprint/09_customer_journey.md`
- Deployment options (API vs Workspace): `docs/architecture/llm_deployment_options.md`
- Eval framework template: `docs/evals/eval_framework_template.md`
- Eval report template: `docs/evals/customer_eval_report_template.md`
- Executive summary template: `docs/sales/executive_summary_template.md`
- Technical deep dive outline: `docs/sales/technical_deep_dive_outline.md`
- Role alignment: `docs/application/role_alignment.md`
- Security & compliance packet: `docs/sales/security_compliance_packet.md`
- LLM Workspace checklist: `docs/sales/llm_workspace_checklist.md`
- RFP requirements matrix: `docs/application/rfp_requirements_matrix.md`
- QBR template: `docs/sales/qbr_template.md`
- Sample scenario (one-pager): `docs/sales/sample_scenario_onepager.md`

## How to run (local)
1) Backend
```
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app
```
Optional local Ollama runtime:
```bash
# terminal A
ollama serve

# terminal B (before backend start)
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b
export LLM_OLLAMA_BASE_URL=http://127.0.0.1:11434
python3 -m app
```
2) Frontend
```
cd app/frontend
npm install
# optional community integrations
# export VITE_FORMSPREE_ENDPOINT="https://formspree.io/f/xxxxxx"
# export VITE_DISQUS_SHORTNAME="your-shortname"
# export VITE_DISQUS_IDENTIFIER="atelier-home"
# export VITE_GISCUS_REPO="owner/repo"
# export VITE_GISCUS_REPO_ID="R_kgxxxx"
# export VITE_GISCUS_CATEGORY="General"
# export VITE_GISCUS_CATEGORY_ID="DIC_kwxxxx"
# optional AdSense
# export VITE_ADSENSE_CLIENT="ca-pub-xxxxxxxxxxxxxxxx"
# export VITE_ADSENSE_SLOT="1234567890"
npm run dev
```
3) Visit `http://localhost:5173`

AdSense review helpers are prepared in `app/frontend/public/ads.txt`, `app/frontend/public/robots.txt`, `app/frontend/public/sitemap.xml`, `app/frontend/public/about.html`, `app/frontend/public/compliance.html`, and `app/frontend/public/_headers`.

## How to run (docker)
```
cd infra
docker-compose up --build
```

## One-command demo (no docker)
If you don't have Docker installed, use the local runner script:
```bash
# auto mode: tries Ollama first, then falls back to stub
make demo-local
```

## Ollama quick start (recommended)
Run a local model and experience the full flow without paid API keys.

```bash
# install Ollama first: https://ollama.com/download
ollama pull llama3.2:latest
make demo-ollama-local
```

The script starts backend + frontend and opens a reviewer-ready local flow on `http://localhost:5173`.

## Value tour (5 minutes)
Use this sequence to feel the service utility, not just feature checkboxes:

1. In Access Control, issue an `Ops` token.
2. Run UC1 with a handover query (for example: "Summarize payment-prod handover risks and next actions").
3. Run UC2 with timeout/error logs and compare generated root causes + runbook steps.
4. Open Scenario Runner and export the report + evidence pack (zip + SHA-256 manifest).
5. Review `/audit/summary` and `/metrics` to verify governance and LLMOps signals.

## Scenario Runner (CLI)
Generate a shareable validation report (Markdown) + evidence pack (zip).

Against an already-running backend:
```bash
make scenario-run
```

One command (auto: Ollama if available, otherwise stub):
```bash
make scenario-demo-local
```

Force Ollama mode:
```bash
make scenario-demo-ollama-local
```

Output is written under `dist/scenario_runs/` (gitignored).

## One-command demo (docker)
```
make demo
```

## Evaluation
- Datasets: `evals/datasets/initial_20.jsonl`, `evals/datasets/starter_50.jsonl`
- Runner: `python3 evals/runner/run_eval.py --dataset evals/datasets/initial_20.jsonl`
- Reports: `evals/reports/latest_report.json`, `evals/reports/latest_report.md`, baseline diff

## Tests
```bash
pytest -q
```

## Backend quality gate
```bash
make quality-backend
```

## Metrics
- Prometheus endpoint: `GET /metrics`
- Request counters, latency histogram, token usage, cost estimates, policy events

## Production Runtime Options (implemented)
- Auth mode:
  - `AUTH_MODE=local_jwt` (default) or `AUTH_MODE=oidc`
  - OIDC verify: `OIDC_ISSUER`, optional `OIDC_AUDIENCE`, optional `OIDC_JWKS_URL`
  - optional login hardening: `DEMO_LOGIN_CODE=<shared-code>` (requires code in `POST /auth/login`)
  - login abuse guard (when login code is enabled): `LOGIN_ATTEMPT_CAPACITY=10`, `LOGIN_ATTEMPT_REFILL_PER_SEC=0.1`
- JWT key rotation:
  - `JWT_ACTIVE_KID=v2`
  - `JWT_SECRETS="v1:old-secret,v2:new-secret"` (or `JWT_SECRETS_FILE` JSON map)
- OIDC token exchange:
  - `POST /auth/oidc/exchange` with `{ "id_token": "..." }`
- LLM provider:
  - `LLM_PROVIDER=stub` (default, offline), `LLM_PROVIDER=ollama`, or `LLM_PROVIDER=openai` / `LLM_PROVIDER=openai_compatible`
  - `LLM_OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`)
  - Ollama local mode (no API key required): `LLM_PROVIDER=ollama`, optional `LLM_MODEL=llama3.2:latest`, optional `LLM_OLLAMA_BASE_URL=http://127.0.0.1:11434`
  - `LLM_OPENAI_API_KEY` (or `LLM_OPENAI_API_KEY_FILE`)
  - optional `LLM_OPENAI_BASE_URL`, `LLM_OPENAI_ORG`
  - reliability fallback: `LLM_FALLBACK_TO_STUB_ON_ERROR=true` (default)
  - circuit breaker: `LLM_CIRCUIT_BREAKER_THRESHOLD=3`, `LLM_CIRCUIT_BREAKER_COOLDOWN_SEC=30`
- Integration auth:
  - `INTEGRATIONS_REQUIRE_AUTH=true` (default)
  - when enabled, `POST /integrations/slack/events` and `POST /integrations/jira/ticket` require `Authorization: Bearer <JWT>`
  - if bearer includes multiple roles, integrations run with highest privilege role (`Admin > Ops > Employee`)
- Request guardrails:
  - `REQUEST_MAX_BODY_BYTES=262144` (default)
  - payloads larger than this return `413 Request body too large`
  - validation failures return a standard `422` envelope with `request_id` and normalized error list
- Ops policy and alerts:
  - `GET /ops/policy`
  - `GET /ops/alerts` and `GET /ops/alerts?deliver=true`
  - optional webhook: `OPS_ALERT_WEBHOOK_URL`
- Event logging hygiene:
  - service event/control-tower contexts are sanitized before persistence (token/secret/password fields are redacted)
- Storage backend:
  - `EVENT_STORAGE_BACKEND=sqlite` (default) or `EVENT_STORAGE_BACKEND=jsonl`
  - JSONL paths: `SERVICE_EVENTS_JSONL_PATH`, `CONTROL_TOWER_DECISIONS_JSONL_PATH`, `DAILY_COST_JSON_PATH`

## Role alignment
- Employee: limited docs
- Ops: ops docs
- Admin: all docs

## Swap-in guidance
- **OIDC/SAML**: replace `/auth/login` with external IdP; validate JWT with IdP public keys
- **LLM API**: implement `LLMAdapter` with provider SDK, map token usage + cost
- **LLM Workspace**: align SSO/SAML and admin policy requirements with enterprise governance
- **Cloud storage**: replace local SQLite and file paths with managed DB/object store

## Pre-Sales Kit Extras
- Discovery Wizard: `python3 app/backend/scripts/discovery_wizard.py`
- ROI Calculator: `python3 app/backend/scripts/roi_calculator.py --handle-time-min 12 --tickets-per-week 800 --hourly-cost 35 --deflection-rate 0.25 --adoption-rate 0.6`
- PoC Success Generator: `python3 app/backend/scripts/poc_success_generator.py`
- BYO Dataset Ingest: `python3 evals/runner/dataset_ingest.py --input evals/datasets/sample_dataset.csv`
- Eval Gate: `make eval-gate`
- Audit Viewer: `python3 app/backend/scripts/audit_viewer.py --log app/backend/data/audit.log` (generated at runtime)
- Exec Deck: `python3 app/backend/scripts/generate_exec_deck.py`
- Modules index: `docs/modules/README.md`
- Integration demo checklist: `docs/sales/integration_demo_checklist.md`
- Red-team summary: `docs/evals/redteam_summary.md`
- Exec dashboard snapshot: `docs/sales/exec_value_dashboard/snapshot.svg`
These proof artifacts and demo scripts are designed to support discovery and PoC alignment in pre-sales conversations.

## UI walkthrough (local)
- Tabs: Overview / Capabilities / Readiness / Scenario Runner / Console
- Scenario Runner: runs JWT -> UC1 -> UC2 -> governance/ops checks and exports a Markdown report
- Console: lets reviewers call UC1/UC2 and load `/audit/summary` and `/ops/runtime` (role-gated)

## Publishing safety (before you push)
This repo is safe to publish: runtime data (SQLite DB, audit log, Chroma persistence) is generated locally and ignored by git.

```bash
make sanitize
```

## KR evals
- KR dataset: `evals/datasets/kr_enterprise_30.jsonl`
- KR eval run: `python3 evals/runner/run_eval.py --dataset evals/datasets/kr_enterprise_30.jsonl`

## Glossary (first-time readers)
- PoC: Proof of Concept
- RBAC: Role-Based Access Control
- PII: Personally Identifiable Information
- RAG: Retrieval-Augmented Generation
- OIDC: OpenID Connect
- IaC: Infrastructure as Code (e.g., Terraform)

<!-- codex:local-verification:start -->
## Local Verification
```bash
make -n
```

## Repository Hygiene
- Keep runtime artifacts out of commits (`.codex_runs/`, cache folders, temporary venvs).
- Prefer running verification commands above before opening a PR.

_Last updated: 2026-03-04_
<!-- codex:local-verification:end -->
