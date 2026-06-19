# Scope

## Mission
Deliver an enterprise-style reference implementation for **Applied AI Architecture Architect, Korea** as a personal project (no real customers; synthetic data only) that proves:
- Enterprise discovery translated into architecture decisions
- Safe enterprise LLM integration (RBAC/SSO concept, audit, PII redaction, injection defense, tool allowlist)
- Evaluation harness (golden set, rubric, regression, report + baseline diff)
- Ops readiness (metrics, reliability controls, usage tracking)
- Architecture assets (demo scripts, objections, MAP, 30/60/90)

## Target Personas
- Enterprise AI technical inspection / solution architect (primary)
- Security/IT (architectures controls)
- Platform/ML Engineering (evaluates integration/ops)

## In-Scope Use Cases (Only 2)
1) **HoneyPot Handover Copilot (RAG)**
   - RAG over ~70 handover docs (synthetic placeholders)
   - Normalize docs into primary JSON schema before embedding
   - Output citations (doc_id + JSON field path)
   - Support **citation-only mode** for sensitive prompts

2) **DevOps Log Intelligence**
   - Paste build/deploy logs -> summarize -> root-cause hypotheses -> recommended runbook steps
   - Tool calling via **allowlist** (local tools only)
   - Default **PII redaction**

## Enterprise Controls (Must Implement)
- Mock login (JWT) with roles: Employee, Ops, Admin
- RBAC enforcement for retrieval by role + metadata filters
- Audit logging (structured JSON, file + stdout) on every request
- PII redaction (input + output) with redacted logs by default
- Prompt injection defenses (context separation, tool allowlist, retrieval constraints, heuristic detector)
- Tool router (allowlist only)
- Pluggable LLM adapter (local stub default; provider via ENV)

## Non-Goals / Out-of-Scope
- Production-grade identity integration (OIDC/SAML) - provide guidance only
- Cloud-managed vector DB or data lake integrations (local dev first)
- Real LLM API integration (pluggable interface only; no claims of live integration)
- Multi-tenant SaaS hardening (single-tenant reference)

## Success Criteria (High-Level)
- UC1/UC2 functional with RBAC, citations, tools, redaction
- Evals harness runs and produces report + baseline diff
- Metrics endpoint and audit logs present required fields
- Local `docker-compose` runs backend + frontend

## Deliverables
- Full repo with backend + frontend + evals + docs + infra
- Architecture artifacts
- Blueprint docs and acceptance criteria
