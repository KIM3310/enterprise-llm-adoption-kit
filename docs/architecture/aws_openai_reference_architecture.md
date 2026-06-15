# AWS + OpenAI Production Reference Architecture (Conceptual)
This document is a **reference architecture** for running the Enterprise LLM Adoption Kit in a real enterprise environment on AWS, using the OpenAI API through the existing adapter (`LLM_PROVIDER=openai`).

Note:
- This repo **implements** only the local demo architecture (FastAPI + Vite + Chroma + SQLite).
- The AWS design below is **conceptual** and provided for project / architecture discussion.
- All datasets and scenarios remain synthetic/hypothetical.

## Goals
- Keep LLM adoption **inspectable** (RBAC, auditability, evals, metrics).
- Ship a PoC that can graduate to production with minimal redesign.
- Make data handling explicit (demo vs enterprise mode).
- Avoid “magic” architecture: every trust boundary has an owner and a control.

## High-Level Diagram
```mermaid
flowchart LR
  U[Technical reader / Operator] -->|HTTPS| CF[CloudFront]
  CF -->|static assets| S3FE[(S3: Frontend)]
  CF -->|/api| ALB[ALB + AWS WAF]

  subgraph VPC["VPC (2+ AZs)"]
    ALB -->|8000| ECS[ECS Fargate: Backend API]
    ECS --> CW[(CloudWatch Logs)]
    ECS --> SM[Secrets Manager]
    ECS --> RDS[(RDS Postgres: events/audit/usage)]
    ECS --> S3AUD[(S3: audit evidence / exports)]
    ECS --> VPCEndpoints[VPC Endpoints\n(S3/ECR/Logs/SM)]
    ECS --> NAT[NAT Gateway / Egress Proxy]
  end

  NAT -->|HTTPS| OAI[OpenAI API]
```

## Recommended AWS Resources (Inventory)
| Layer | Resource | Purpose | Notes |
| --- | --- | --- | --- |
| Edge | CloudFront | Serve UI + route `/api` to ALB | Optional, but improves TLS + caching |
| Edge | AWS WAF | Basic protection | Rate-limit + block common patterns |
| Networking | VPC (2+ AZ) | Isolation + routing | Public subnets for ALB, private for ECS/RDS |
| Networking | VPC Endpoints | Reduce public egress | S3, ECR (api+dkr), CloudWatch Logs, Secrets Manager |
| Compute | ECS Fargate | Run backend service | Private subnets, no public IP |
| Compute | ECR | Store images | Built by CI, deployed to ECS |
| Data | RDS Postgres | Durable event/audit/usage store | Replace SQLite for production |
| Data | S3 (Audit/Exports) | Evidence packs / exports | Optional Object Lock for WORM |
| Secrets | Secrets Manager + KMS | Store OpenAI key + JWT secrets | Key rotation policy + tight IAM |
| Observability | CloudWatch | Logs + basic metrics | Add alarms (error rate, latency, usage) |
| Observability (optional) | AMP/Grafana or Datadog | Prometheus `/metrics` scraping | Keep `/metrics` behind auth in production |
| Identity | Corporate IdP (OIDC) | SSO | Backend already supports `AUTH_MODE=oidc` |

## Networking & Security (What Makes This “Enterprise”)
### Subnets and traffic
- **Public subnets**: ALB (ingress only).
- **Private subnets**: ECS tasks, RDS, internal services.
- **No public IPs** on tasks.
- Use **VPC endpoints** for AWS services so “AWS-to-AWS” traffic stays private.

### Egress (OpenAI calls)
You still need outbound HTTPS for OpenAI.
Options (in order of maturity):
1. NAT Gateway (simplest) + security group egress allowlist (coarse).
2. Egress proxy (Squid / Envoy) with domain allowlist + logging.
3. AWS Network Firewall with TLS SNI rules (advanced; still not perfect for SaaS IPs).

### Secrets & key management
- Store `LLM_OPENAI_API_KEY` in **Secrets Manager**, encrypted with **KMS**.
- Avoid plaintext env vars in task definitions. Prefer ECS secrets injection.
- Rotate JWT signing keys via `JWT_SECRETS`/`JWT_ACTIVE_KID` strategy already present in this repo.

### Identity (SSO)
- Use `AUTH_MODE=oidc` with your corporate IdP.
- Keep “local_jwt” as dev-only.
- Enforce role mapping from IdP groups (`OIDC_*` env vars + claim mapping).

### Data handling modes
- `DATA_HANDLING_MODE=demo`: store raw prompts/outputs (local only).
- `DATA_HANDLING_MODE=enterprise`: store hashed audit entries (recommended).

## CI/CD (GitHub Actions -> AWS)
### Build & test
- Backend quality gate (already in repo) should be a required check.
- Frontend `vite build` should be a required check.
- Eval gate should fail PRs that degrade baseline quality.

### Deploy (recommended pattern)
1. CI builds images and pushes to ECR (tag by commit SHA).
2. Terraform applies infra (VPC/ECS/ALB/etc) in a controlled environment.
3. Deploy step updates ECS task definition to the new image tag.
4. Optional: invalidate CloudFront cache for UI releases.

### Credentials (no long-lived keys)
- Use GitHub Actions **OIDC** to assume an AWS role:
  - Minimal permissions for ECR push + ECS service update + Terraform state backend.

## Mapping to This Repo (Runtime Configuration)
Backend env vars you would set via ECS task definition:
- `AUTH_MODE=oidc` (or `local_jwt` for dev)
- `OIDC_ISSUER=...`
- `OIDC_AUDIENCE=...` (optional)
- `OIDC_JWKS_URL=...` (optional)
- `JWT_ISSUER=enterprise-llm-adoption-kit`
- `JWT_SECRETS=...` and `JWT_ACTIVE_KID=...`
- `LLM_PROVIDER=openai`
- `LLM_OPENAI_API_KEY` injected from Secrets Manager
- `EVENT_STORAGE_BACKEND=sqlite|jsonl` (production should move to a DB-backed implementation)

## Terraform Draft
An IaC draft for this architecture is included at:
- `infra/aws/terraform`

It is intentionally conservative:
- Secure defaults, placeholder secrets, and no production claims.
- Designed for operators to inspect, not for a “one click prod deploy.”

