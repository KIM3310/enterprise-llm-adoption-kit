# Security Threat Model

## Scope
Covers data ingress (user inputs, logs, docs), retrieval pipeline, tool execution, LLM prompts/responses, audit/metrics storage, and UI/API access.

## Threat Modeling Approach
- STRIDE-oriented analysis
- Focus on prompt injection, data exfiltration, and RBAC bypass

## Threats & Mitigations (Selected)

### Spoofing
- **Threat**: Impersonation via forged JWT
- **Mitigation**: Signed JWT with short TTL; role claims validated server-side; mocked auth with clear swap path to OIDC/SAML
- **Additional guard**: integration endpoints (`/integrations/slack/events`, `/integrations/jira/ticket`) require bearer JWT by default

### Tampering
- **Threat**: Prompt injection in retrieved documents
- **Mitigation**: Context separation; injection heuristic detector; retrieval chunk caps; citation-only mode for sensitive prompts

### Repudiation
- **Threat**: No audit trail of actions
- **Mitigation**: JSON audit logs with request_id, user_id, roles, use_case, tool_calls, policy_events

### Information Disclosure
- **Threat**: PII leaks in inputs/outputs/logs
- **Mitigation**: Regex PII redaction on input + output; only redacted payloads stored in logs

### Denial of Service
- **Threat**: Excessive requests or long prompts
- **Mitigation**: Rate limiting token bucket; max input size; latency budget alarms

### Elevation of Privilege
- **Threat**: Role bypass for restricted docs
- **Mitigation**: Enforced RBAC filter in retrieval layer; server-side claims validation

## Policy / Controls List (Minimum)
1) **RBAC Enforcement** at retrieval time (Admin/Ops/Employee)
2) **PII Redaction** (input/output) with redacted logs only
3) **Prompt Injection Defense** (context separation + heuristic detection)
4) **Tool Allowlist** (deny unknown tools, log policy_events)
5) **Citation-Only Mode** for sensitive prompts
6) **Audit Logging** with required fields
7) **Rate Limiting** per user/role/use_case

## Trust Boundaries
- Browser <-> Backend API
- Backend <-> Vector Store / SQLite / File Store
- Backend <-> External LLM Provider

## Residual Risks
- Deterministic stub LLM may not mirror real LLM behavior
- Regex PII detection is baseline only (no ML-based PII detection)
- Local dev storage lacks enterprise encryption-at-rest controls
