# Demo Script (Engineering, 10 min)

## Objective
Walk through architecture, safety controls, evals, and observability.

## Agenda
1) Architecture overview and trust boundaries
2) UC1 RAG with citations and RBAC
3) UC2 tool calling and redaction
4) Audit logs, metrics, and rate limiting
5) Evals harness and baseline diff

## Steps
1) **Architecture (2 min)**
   - Show `docs/blueprint/02_architecture.md`
   - Explain trust boundaries and data flow

2) **Auth + RBAC (1 min)**
   - Login as Employee vs Admin
   - Show document access differences
   - OIDC mock login:
     ```bash
     curl -s http://localhost:8000/auth/oidc/login -H 'Content-Type: application/json' -d @app/backend/data/samples/oidc_claims_sample.json
     ```

3) **Integrations (2 min)**
   - Slack webhook:
     ```bash
     curl -s http://localhost:8000/integrations/slack/events -H 'Content-Type: application/json' -d @app/backend/data/samples/slack_event_sample.json
     ```
   - Jira ticket:
     ```bash
     curl -s http://localhost:8000/integrations/jira/ticket -H 'Content-Type: application/json' -d @app/backend/data/samples/jira_ticket_sample.json
     ```

4) **UC1 RAG (2 min)**
   - Query with citation-only mode off
   - Highlight citations with doc_id and field_path
   - Toggle citation-only mode

5) **UC2 Log Intelligence (2 min)**
   - Paste logs with PII
   - Show redaction and tool calls
   - Show runbook steps from local store

6) **Observability (1 min)**
   - `GET /metrics`
   - Show audit log schema

7) **Evals (2 min)**
   - Run eval runner
   - Open report.md and baseline diff
