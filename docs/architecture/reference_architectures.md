# Reference Architectures
See `docs/architecture/llm_deployment_options.md` for API vs Workspace guidance.
See `docs/architecture/integration_patterns.md` for common enterprise patterns.

## Implemented (This Repo)
- Local dev: FastAPI + Vite + Chroma + SQLite
- Mock JWT RBAC, audit logs, redaction, eval runner

## SaaS (Conceptual)
- Managed LLM API via adapter
- Managed vector DB + object storage
- Centralized observability + SIEM integration

## VPC / PrivateLink-like (Conceptual)
- Private endpoints between app and model provider
- Network segmentation and egress allowlist
- Customer-managed keys and dedicated logging pipeline

## On-Prem Connector (Conceptual)
- Data connector to on-prem KB/runbooks
- Local embedding + retrieval, outbound model calls only
- Strict data handling and retention policies

Note: Only the local dev architecture is implemented in this repo. Others are conceptual.
