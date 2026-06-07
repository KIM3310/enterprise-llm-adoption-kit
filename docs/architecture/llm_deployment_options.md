# LLM Deployment Options (API vs Workspace)

Purpose: help define a hypothetical enterprise adoption path and align on governance, security, and delivery expectations.

## Option A: LLM API (Custom apps)
Best when you need custom workflows, system integrations, or productized experiences.

Typical characteristics
- Custom UI/UX and workflow orchestration
- Tool calling and system-specific automation
- Flexible integration with internal data and services
- Clear ownership of evals, deployment, and reliability

Key controls to plan
- Identity: OIDC/SAML via external IdP
- RBAC and audit logging
- Prompt/response redaction and policy filters
- Evals and regression gates per use case
- Cost, latency, and reliability monitoring

## Option B: LLM Workspace (Enterprise SaaS)
Best when rapid adoption for knowledge workers is the priority.

Typical characteristics
- Faster rollout for internal users
- Lower engineering effort for initial access
- Policy and governance managed at the admin layer
- Useful for discovery, internal enablement, and early ROI

Key controls to plan
- Identity: SSO/SAML and user lifecycle (SCIM if available)
- Admin policies for access and acceptable use
- Data handling and retention rules
- Adoption tracking and value measurement

## Decision matrix (high level)
| Criteria | LLM API | LLM Workspace |
|---|---|---|
| Custom workflow + automation | Strong | Limited |
| Time-to-first-value | Medium | Fast |
| Engineering effort | Higher | Lower |
| Governance depth | High (customizable) | High (admin policy driven) |
| Use case fit | Product/ops automation | Knowledge worker enablement |

## Hybrid path (recommended in many enterprises)
- Start with the Workspace to enable internal teams and gather early feedback
- Use API for prioritized workflows or external-facing use cases (planning)
- Reuse evals and safety policies across both paths to keep standards consistent

## Evidence in this repo
- Discovery artifacts: `docs/review_assets/discovery_questionnaire.md`, `docs/review_assets/korea_stakeholder_map.md`
- Architecture + security: `docs/blueprint/02_architecture.md`, `docs/blueprint/03_security_threat_model.md`
- Evals: `docs/blueprint/04_evals_plan.md`, `docs/evals/eval_design.md`
- Integration patterns: `docs/modules/integration-pack/README.md`
- Workspace checklist: `docs/review_assets/llm_workspace_checklist.md`

Note: This doc is a decision and planning guide. It does not claim any live integration.
