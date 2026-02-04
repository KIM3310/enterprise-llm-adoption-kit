# LLMOps Plan

## Objectives
- Provide observability for latency, usage, reliability, and cost
- Enforce reliability controls (rate limiting, retries)
- Track policy events and compliance

## Metrics (Prometheus)
- **Request Counters**: total by use_case, role, status
- **Latency Histogram**: p50/p95/p99 by endpoint
- **LLM Tokens**: tokens_in/out by use_case
- **Cost Estimate**: USD per request and daily aggregates
- **Policy Events**: redaction_applied, injection_detected, allowlist_denied

## SLO Targets
- **Availability**: 99% (local demo baseline)
- **Latency**: p95 < 2.5s for UC2, p95 < 3.5s for UC1
- **Error Rate**: < 2% overall
- **RBAC Violations**: 0 tolerated

## Alerts (Example Thresholds)
- Error rate > 5% over 5m
- p95 latency > 5s for 10m
- Injection detected > 3% of requests
- Cost/day > configured budget threshold

## Reliability Controls
- Token bucket **rate limiting** per user/role/use_case
- **Retry/backoff** for transient LLM failures
- **Timeouts** on tool execution

## Logging & Audit
- Structured JSON logs (file + stdout)
- Only redacted payloads stored in logs

