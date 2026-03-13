# Jira Integration (Mock Ticket Summary)

## Endpoint
`POST /integrations/jira/ticket`

## Example
```bash
TOKEN=$(curl -s http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"demo-ops","role":"Ops"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s http://localhost:8000/integrations/jira/ticket \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d @app/backend/data/samples/jira_ticket_sample.json
```

## Output
Returns a `comment` payload with summary, root causes, and next steps for the ticket.
