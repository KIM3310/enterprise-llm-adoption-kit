# Demo Checklist (Golden Screenshots)

## Goal
Capture 5 screenshots that prove enterprise readiness.

## Screenshots
1) RBAC
   - Login as Employee vs Admin, show different citations
   - File name: 00_rbac.png
2) Citations
   - UC1 response with doc_id + field_path
   - File name: 01_citations.png
3) Audit Logs
   - Show JSON audit entry with policy_events
   - File name: 02_audit_log.png
4) Eval Report
   - Show `evals/reports/latest_report.md`
   - File name: 03_eval_report.png
5) Metrics
   - Show `/metrics` output in browser
   - File name: 04_metrics.png

## Commands
```
cd infra
docker compose up --build
```

