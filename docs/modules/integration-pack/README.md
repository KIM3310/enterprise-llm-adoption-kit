# Module — Enterprise Integration Pack

Focus: mock SSO/OIDC login, Slack-style webhook, and Jira ticket workflow while preserving existing UC1/UC2 behavior.

## Run (local)
- Start backend: `python3 -m app`
- OIDC login: `POST /auth/oidc/login`
- Slack events: `POST /integrations/slack/events`
- Jira tickets: `POST /integrations/jira/ticket`

## Samples
See `samples/` and `docs/` for payloads and walkthroughs.

Related guidance: `docs/architecture/integration_patterns.md`.
