# Engineering Talk Track (10 minutes)

## Goal
Demonstrate architecture decisions, controls, evals, and ops readiness.

## Steps (with commands)
1) Start stack:
```
cd infra
docker compose up --build
```
2) Auth + RBAC
- UI: role switch between Employee/Ops/Admin
- Expected: citations differ by role

3) UC1 RAG
- Query: "Summarize handover risks for payments prod"
- Show citations with doc_id + field_path
- Toggle citation-only mode
- Evidence: `demo_screenshots/01_citations.txt`

4) UC2 Log Intelligence
- Paste log with PII: "Contact test@example.com"
- Show redaction + tool calls
- Evidence: `demo_screenshots/11_slack.svg` or `demo_screenshots/12_jira.svg`

5) Audit + Metrics
- Metrics: http://localhost:8000/metrics
- Audit log: `app/backend/data/audit.log`
- Evidence: `demo_screenshots/04_metrics.txt`, `demo_screenshots/14_metrics.svg`, `demo_screenshots/02_audit_log.txt`, `demo_screenshots/13_audit.svg`

6) Evals + Gate
```
python3 evals/runner/run_eval.py --dataset evals/datasets/initial_20.jsonl
python3 evals/runner/eval_gate.py --min-safety 3.0 --min-groundedness 3.0
```
- Screenshot: "05_eval_report.png"
- Evidence: `demo_screenshots/03_eval_report.txt`

## Closing
- Pluggable LLM adapter
- Clear swap paths for IdP and storage
- Observable, testable, and safe by design
