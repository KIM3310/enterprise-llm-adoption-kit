# PoC → Production Playbook (Summary)

## 1) Governance & Security
- Confirm data handling mode (demo vs enterprise)
- Retention and audit logging requirements
- PIPA/K-ISMS alignment review

## 2) Architecture & Connectivity
- Select deployment: SaaS, VPC/PrivateLink-like, or on-prem connector
- Validate network segmentation and egress controls

## 3) Model & Policy
- Configure model provider adapter
- Define safety guardrails and refusal policies
- Validate tool allowlist and RBAC

## 4) Reliability & LLMOps
- SLOs: latency, error rate, cost thresholds
- Alerting and escalation path
- Eval gate in CI for regressions

## 5) Rollout Plan
- PoC → limited pilot → production (planning sequence)
- Stakeholder training and runbooks
- Success criteria checkpoint
