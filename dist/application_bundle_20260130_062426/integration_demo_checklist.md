# Integration Demo Checklist (3-min)

## Screenshots (5)
1) OIDC mock login (JWT issued)
   - File: `10_oidc.svg`
2) Slack webhook UC1 response
   - File: `11_slack.svg`
3) Jira ticket comment response
   - File: `12_jira.svg`
4) Audit log entry (integration call)
   - File: `13_audit.svg`
5) Metrics endpoint snapshot
   - File: `14_metrics.svg`

## Commands
```bash
curl -s http://localhost:8000/auth/oidc/login   -H 'Content-Type: application/json'   -d @app/backend/data/samples/oidc_claims_sample.json

curl -s http://localhost:8000/integrations/slack/events   -H 'Content-Type: application/json'   -d @app/backend/data/samples/slack_event_sample.json

curl -s http://localhost:8000/integrations/jira/ticket   -H 'Content-Type: application/json'   -d @app/backend/data/samples/jira_ticket_sample.json

python3 app/backend/scripts/audit_viewer.py --log app/backend/data/audit.log
curl -fsS http://localhost:8000/metrics | head -n 20
```
