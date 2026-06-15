# Common Objections (LLM Adoption) + Responses

## Privacy / Data Residency
- Objection: "We need KR data residency and strict retention."
- Response: "Data handling modes support redaction or hash-only storage; retention is enforced in enterprise mode. Reference architectures include KR-region/VPC models."

## Hallucinations / Safety
- Objection: "We cannot ship hallucinations."
- Response: "RAG with citations, eval gates, and regression diff are built in. Safety and groundedness thresholds are enforced before rollout."

## Integration Effort
- Objection: "Integration takes too long."
- Response: "Adapter pattern, mock JWT, and local vector DB let teams validate quickly; swap guides for OIDC/SAML and LLM API are included."

## Cost Predictability
- Objection: "LLM usages are unpredictable."
- Response: "Per-request usage tracking, aggregated daily totals, and Impact calculator are included."

## Security Governance
- Objection: "Security team will block it."
- Response: "RBAC, audit logs, tool allowlist, PII redaction, and injection defenses are implemented and visible."
