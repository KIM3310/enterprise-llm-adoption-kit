# Security Governance

## Control Objectives
- Ensure authorized access via RBAC
- Prevent PII leakage
- Detect and log prompt injection attempts
- Enforce tool allowlist
- Maintain full audit trail

## Controls Mapping
- **RBAC**: enforced at retrieval and tool layers
- **PII Redaction**: input/output redaction with redacted logs only
- **Prompt Injection Defense**: context separation + heuristic detector
- **Tool Allowlist**: deny unknown tools and log policy events
- **Audit Logging**: JSON lines to file and stdout

## Compliance Notes
- Local demo storage only; no production claims
- Swap guidance for OIDC/SAML and managed storage

