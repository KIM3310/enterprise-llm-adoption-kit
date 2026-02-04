# PoC Success Criteria

## Functional
- UC1 returns citations and respects RBAC filters
- UC2 uses allowlisted tools and returns runbook steps

## Safety
- PII redaction applied to input and output
- Prompt injection attempts detected and logged
- Audit logs emitted per request with required fields

## Evaluation
- Evals runner produces report.json and report.md
- Baseline diff highlights regressions or gains

## Operations
- /metrics exposes request counters and latency histogram
- Rate limiting blocks excessive usage

