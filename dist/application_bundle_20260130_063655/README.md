# Enterprise LLM Adoption Kit (Korea)
Tagline: Discovery -> Secure Architecture -> Evals -> Deployment/LLMOps
Note: This is a personal portfolio project. No real customers or production deployments are represented; all data and scenarios are synthetic or hypothetical.

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
```

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
2) Frontend
```
cd app/frontend
npm install
npm run dev
```
3) Visit `http://localhost:5173`

## How to run (docker)
```
cd infra
docker-compose up --build
```

## One-command demo
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

## Metrics
- Prometheus endpoint: `GET /metrics`
- Request counters, latency histogram, token usage, cost estimates, policy events

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
- Audit Viewer: `python3 app/backend/scripts/audit_viewer.py --log app/backend/data/audit.log`
- Exec Deck: `python3 app/backend/scripts/generate_exec_deck.py`
- Modules index: `docs/modules/README.md`
 - Integration demo checklist: `docs/sales/integration_demo_checklist.md`
 - Red-team summary: `docs/evals/redteam_summary.md`
 - Exec dashboard snapshot: `docs/sales/exec_value_dashboard/snapshot.svg`
These proof artifacts and demo scripts are designed to support discovery and PoC alignment in pre-sales conversations.

## Pre-Sales UI + KR Evals
- UI tab: "Discovery & Audit" (loads `/audit/summary`)
- KR dataset: `evals/datasets/kr_enterprise_30.jsonl`
- KR eval run: `python3 evals/runner/run_eval.py --dataset evals/datasets/kr_enterprise_30.jsonl`
