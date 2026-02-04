# Modules Index

## Module 1 — Pre-Sales PoC Kit (Core)
- Core repo (root)
- Proof: README `Proof` section

## Module 2 — Enterprise Integration Pack
- Folder: `docs/modules/integration-pack/`
- Endpoints: `/auth/oidc/login`, `/integrations/slack/events`, `/integrations/jira/ticket`
- Samples: `app/backend/data/samples/`

## Module 3 — Workshop-in-a-Box
- Folder: `docs/modules/workshop-box/`
- Generator: `python3 app/backend/scripts/run_workshop.py`
- Snapshot: `python3 app/backend/scripts/capture_workshop_outputs.py`

## Module 4 — Red Team & Safety Eval Pack
- Folder: `docs/modules/redteam-pack/`
- Dataset: `evals/datasets/redteam_50.jsonl`
- Baseline: `python3 evals/runner/create_baseline.py --dataset evals/datasets/redteam_50.jsonl --output evals/reports/redteam_baseline.json`

## Module 5 — PoC → Production Playbook
- Folder: `docs/modules/production-playbook/`
- Exec dashboard: `python3 app/backend/scripts/generate_exec_dashboard.py`
