# Architecture Guide - Enterprise LLM Adoption Kit

Updated: 2026-05-30

Use this page as the short path through the repository. It keeps the architecture grounded in the code, docs, commands, and boundaries that are already present.

## Summary

| Field | Notes |
|---|---|
| Lane | Enterprise AI governance |
| Core idea | Governance toolkit with RBAC, redaction, prompt-injection checks, evals, and rollout controls. |
| Primary reader | Enterprise AI, IT governance, security, platform, and operations teams. |
| Stack | Terraform, Docker |

## Open First

1. Start with the README fast path and architecture section.
2. Open `docs/service-launch-playbook.md` only when architectureing the product or service angle.
3. Check the commands below before making claims about quality.
4. Skim the CI workflows and fixture data before deeper implementation architecture.
5. Read the boundaries section before presenting the project externally.

## Checks

| Purpose | Command |
|---|---|
| Full local gate | `make verify` |

## CI

- .github/workflows/architecture-blueprint.yml
- .github/workflows/backend-quality-gate.yml
- .github/workflows/ci.yml
- .github/workflows/dependency-architecture.yml
- .github/workflows/docker-publish.yml
- .github/workflows/pages-auto-deploy.yml
- .github/workflows/production-smoke.yml
- .github/workflows/repository-health.yml
- .github/workflows/repository-surface.yml
- .github/workflows/secret-scan.yml
- .github/workflows/security-scan.yml

## Evidence

- infrastructure-as-code architecture surface
- containerized delivery path
- make verify passes
- Architecture assets are current
- Governance controls are demonstrable

## Architecture Notes

| Possible offer | Working scope assumption |
|---|---|
| Adoption workshop | Scope after product intake |
| Governance starter implementation | Scope after product intake |
| Security/eval pack | Scope after product intake |

## Boundaries

- Synthetic data by default
- Customer adapters need scoped auth
- No compliance certification claims without audit

## Useful Metrics

- Policy coverage
- Eval pass rate
- Adoption readiness score
