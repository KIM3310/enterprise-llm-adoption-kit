# HoneyPot Handover JSON Schema

```json
{
  "doc_id": "HP-0001",
  "title": "Payments Handover PROD #0001",
  "system": "payments",
  "env": "prod",
  "access_group": "ops",
  "owner": {
    "name": "Owner-1",
    "team": "Team-1",
    "contact": "owner1@example.com"
  },
  "summary": "Handover summary for payments in prod...",
  "handover_notes": "Recent changes include patch...",
  "runbook_steps": [
    "Check service health dashboard",
    "Validate recent deploy diff",
    "Rollback if error rate exceeds threshold"
  ],
  "dependencies": ["redis", "postgres", "kafka"],
  "risks": ["traffic spike", "dependency outage"],
  "last_updated": "2025-12-10"
}
```

## Notes
- `access_group` drives RBAC filtering
- Citations include `doc_id` and `field_path`

