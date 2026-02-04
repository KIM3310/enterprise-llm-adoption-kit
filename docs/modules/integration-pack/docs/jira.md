# Jira Integration (Mock Ticket Summary)

## Endpoint
`POST /integrations/jira/ticket`

## Example
```bash
curl -s http://localhost:8000/integrations/jira/ticket \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/jira_ticket_sample.json
```

## Output
Returns a `comment` payload with summary, root causes, and next steps for the ticket.
