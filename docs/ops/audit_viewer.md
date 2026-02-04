# Audit Viewer

## Purpose
Summarize audit logs for requests, policy events, tools used, top users, and cost totals.

## Usage
```
python3 app/backend/scripts/audit_viewer.py --log app/backend/data/audit.log
```

## Output
- CLI summary: requests, cost total, top users, tools used, policy events

## API (UI Integration)
- `GET /audit/summary` returns the same summary used by the UI tab
