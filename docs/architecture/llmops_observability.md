# LLMOps Observability

## Metrics
- requests_total{endpoint,use_case,role,status}
- request_latency_seconds{endpoint,use_case}
- llm_tokens_in_total{use_case}
- llm_tokens_out_total{use_case}
- llm_cost_usd_total{use_case}
- policy_events_total{event}

## Logs
- Structured JSON logs with request_id, user_id, roles, use_case, model_config
- Redacted input/output stored by default

## Reliability Controls
- Token bucket rate limiting
- Retry/backoff for transient LLM failures
- Tool execution timeouts (future)

