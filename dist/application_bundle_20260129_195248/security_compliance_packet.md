# Security & Compliance Packet (FAQ)

Use this packet for enterprise security reviews. This is a template.

## Data handling & privacy
- What data is sent to the model?
- How is PII handled? (redaction, minimization)
- Where is data stored and for how long?
- How is access controlled?

## Identity & access
- SSO/SAML/OIDC integration approach
- RBAC model (roles, least privilege)
- Admin auditability

## Audit & monitoring
- Audit log contents and retention
- Monitoring/alerting approach
- Incident response workflow

## Security controls
- Prompt injection defenses
- Tool allowlisting
- Content filtering and refusal rules
- Rate limiting and abuse protection

## Compliance mapping (example)
- SOC2: Access logs, change control, audit trails
- ISO 27001: Risk register + access control
- GDPR/PII: Redaction and data minimization

## Evidence in this repo
- Threat model: `docs/blueprint/03_security_threat_model.md`
- Security governance: `docs/architecture/security_governance.md`
- Audit logs: `app/backend/data/sample_audit.json`
- Safety guardrails: `docs/architecture/safety_guardrails.md`
