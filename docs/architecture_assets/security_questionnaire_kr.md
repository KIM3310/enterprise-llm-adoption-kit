# Security Questionnaire (Template)

본 문서는 합성 시나리오용 템플릿입니다(실제 고객 없음).

## Data Governance
- Data classification (PII/PHI/financial/internal)?
- Data residency requirements (KR region, on-prem)?
- Retention period and deletion SLA?

## Compliance & Standards
- K-ISMS coverage required?
- PIPA handling and consent requirements?
- 금융보안원/전자금융감독규정 적용 여부?

## Access Control
- Required IdP (OIDC/SAML)?
- RBAC/ABAC model expectations?
- Least-privilege and audit requirements?

## Network & Infrastructure
- VPC/PrivateLink-like connectivity needed?
- On-prem connector requirements?
- Egress controls and allowlist policy?

## Logging & Monitoring
- Required log fields for audit?
- SIEM integration expectations?
- Alerting thresholds for security events?

## Model Safety
- Prompt injection defense requirements?
- Tool allowlist policy and change control?
- Redaction/DLP expectations?
