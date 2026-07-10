# Exercise 3 — Security Review

- Architecture guardrails (RBAC, redaction, injection defense)
- Inspect audit log and metrics

Commands:
```bash
curl -fsS http://localhost:8000/metrics | head -n 20
python3 app/backend/scripts/audit_viewer.py --log app/backend/data/audit.log
```
