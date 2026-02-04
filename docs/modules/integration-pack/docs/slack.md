# Slack Integration (Mock Webhook)

## Endpoint
`POST /integrations/slack/events`

## Commands
- `/uc1 <handover query>` → RAG summary + citations
- `/uc2 <log text>` → summary + root causes + runbook steps

## Example
```bash
curl -s http://localhost:8000/integrations/slack/events \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/slack_event_sample.json
```

## Output
Returns a Slack-style `text` response for demo. Audit logs and metrics are recorded.
