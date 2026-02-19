# Acceptance Tests (Black-Box)

## Pre-req
- `docker-compose up` launches backend + frontend
- Backend at `http://localhost:8000`

## Test Cases

### AT-01: Login Issues JWT
- **Step**: POST `/auth/login` with user_id + role
- **Expect**: 200 with JWT; role claim matches request

### AT-02: UC1 RBAC Filters Retrieval
- **Step**: Call `/uc1/handover` as Employee
- **Expect**: citations only from docs with access_groups=employee
- **Negative**: Admin should see superset

### AT-03: UC1 Citation-Only Mode
- **Step**: Call `/uc1/handover?citation_only=true`
- **Expect**: Response contains only citations + minimal template, no raw sensitive text

### AT-04: UC2 Tool Allowlist
- **Step**: Call `/uc2/log-intel` with logs that trigger tools
- **Expect**: audit log shows tool_calls only from allowlist

### AT-05: PII Redaction Input/Output
- **Step**: Include email/phone in prompt
- **Expect**: output redacted; audit log contains redacted input/output

### AT-06: Injection Detection Event
- **Step**: Include prompt injection pattern in logs
- **Expect**: policy_events includes injection_detected=true

### AT-07: Metrics Endpoint
- **Step**: GET `/metrics`
- **Expect**: Prometheus format counters + histogram present

### AT-08: Eval Runner
- **Step**: Run eval runner CLI
- **Expect**: Generates report.json + report.md + baseline diff

### AT-09: Integration Auth Boundary
- **Step**: Call `/integrations/slack/events` and `/integrations/jira/ticket` without bearer token
- **Expect**: 401 when `INTEGRATIONS_REQUIRE_AUTH=true` (default)
