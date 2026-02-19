# SPEC — Project 2: Enterprise Integration Pack

## Goals
- Provide mock SSO/OIDC login that issues app JWT with role claims.
- Add Slack-style webhook endpoint to route `/uc1` and `/uc2` commands.
- Add Jira ticket endpoint to summarize incidents via UC2.
- Ensure audit logs and metrics are recorded for integration flows.

## Non-Goals
- No real OAuth flows or vendor SDKs.
- No external network calls or secrets.

## Key Endpoints
- `POST /auth/oidc/login` → JWT with mapped roles
- `POST /integrations/slack/events` → UC1/UC2 routing (Bearer JWT required by default)
- `POST /integrations/jira/ticket` → UC2 summary for ticket comments (Bearer JWT required by default)

## Data Contracts
- OIDC claims: `sub`, `email`, `groups[]`, `roles[]`
- Slack events: `user_id`, `text`, `channel`, `role`
- Jira tickets: `ticket_id`, `title`, `description`, `priority`, `reporter`, `role`

## Observability
- Reuse existing audit logging from UC1/UC2.
- Record integration endpoint metrics via `requests_total` and `request_latency_seconds`.
