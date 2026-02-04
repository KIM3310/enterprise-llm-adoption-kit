# Demo Runbook (3‑min + 10‑min)

## 3‑min Exec Flow
1) UC1 Handover (with citations)
2) Audit log proof
3) Metrics snapshot

Commands:
```bash
make demo
```

## 10‑min Engineer Flow (with integrations)
1) OIDC mock login
2) Slack UC1 command
3) Jira ticket summary
4) Audit + metrics
5) Evals

Commands:
```bash
curl -s http://localhost:8000/auth/oidc/login \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/oidc_claims_sample.json

curl -s http://localhost:8000/integrations/slack/events \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/slack_event_sample.json

curl -s http://localhost:8000/integrations/jira/ticket \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/jira_ticket_sample.json

curl -fsS http://localhost:8000/metrics | head -n 20
python3 evals/runner/run_eval.py --dataset evals/datasets/initial_20.jsonl
```
