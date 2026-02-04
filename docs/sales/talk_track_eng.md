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
- Screenshot: "01_uc1_citations.png"

4) UC2 Log Intelligence
- Paste log with PII: "Contact test@example.com"
- Show redaction + tool calls
- Screenshot: "02_uc2_tools.png"

5) Audit + Metrics
- Metrics: http://localhost:8000/metrics
- Audit log: `app/backend/data/audit.log`
- Screenshot: "03_metrics.png", "04_audit_log.png"

6) Evals + Gate
```
python3 evals/runner/run_eval.py --dataset evals/datasets/initial_20.jsonl
python3 evals/runner/eval_gate.py --min-safety 3.0 --min-groundedness 3.0
```
- Screenshot: "05_eval_report.png"

## Closing
- Pluggable LLM adapter
- Clear swap paths for IdP and storage
- Observable, testable, and safe by design

