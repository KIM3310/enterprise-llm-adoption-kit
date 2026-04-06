# Enterprise LLM Adoption Kit

[![CI](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml)
[![Security Scan](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml)
[![Docker](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

End-to-end enterprise LLM adoption kit covering discovery, secure architecture, evals, and LLMOps. All data and rollout scenarios are synthetic — the goal is a reviewable, runnable validation kit.

Demo video: https://youtu.be/yMq03b0js0E

## Hiring Fit And Proof Boundary

- **Best fit roles:** solution architect, applied AI engineer, enterprise AI / field engineering
- **Strongest public proof:** governance pipeline, eval harness, observability surfaces, and deployment-ready backend/frontend split
- **What is real here:** RBAC, safety pipeline, audit logging, metrics, integration adapters, CI/CD, and deployment scaffolding
- **What is bounded here:** review cases and documents are synthetic, and Snowflake / Databricks / Bedrock integrations are env-gated

## Latest Verified Snapshot

- **Verified on:** 2026-04-07
- **Command:** `make verify`
- **Outcome:** passed locally; syntax check, dependency check, pytest, smoke diagnostics, and frontend production build completed with 84.20% backend coverage
- **Notes:** `make verify` bootstraps the Python 3.11 backend venv and installs missing frontend dependencies automatically, and Snowflake adapter plus Snowflake-focused service-brief tests were rerun successfully from `app/backend/.venv`

## Datadog-Ready Pack

- Datadog-ready resource pack: [`docs/datadog/README.md`](docs/datadog/README.md)
- Existing env hooks already reserve a Datadog integration lane in `.env.example`
- Current state: asset sync and OTLP wiring are prepared, but live tenant integration is intentionally disabled by default
- Best use: show how enterprise LLM governance, audit, latency, and rollout readiness would be observed in one operator-facing Datadog surface

## Key Capabilities

- **RBAC** enforced at retrieval time (Employee / Ops / Admin roles)
- **Prompt injection detection** and safety refusal rules
- **PII redaction** and audit logging with enterprise-mode hashing
- **RAG retrieval** (Chroma + deterministic hash embeddings)
- **Evals harness** with reports and baseline diffs
- **LLMOps metrics** — latency, tokens, cost, policy events via Prometheus
- **Snowflake integration** — eval results and audit logs (env-var gated)
- **Databricks integration** — MLflow experiment tracking and Delta audit tables (env-var gated)
- **AWS Bedrock** runtime mode alongside stub, OpenAI, Ollama
- **Kubernetes-ready** with HPA, TLS ingress, AlertManager rules

## Architecture

```
Ingress (TLS)  →  FastAPI Backend (RBAC / RAG / Safety / Audit)
                        ↓                    ↓
                 LLM Provider          Snowflake / Databricks
              (OpenAI / Ollama /        (eval + audit persistence)
               Bedrock / stub)
                        ↓
              Prometheus + Grafana + OpenTelemetry
```

Every request passes through four governance layers: RBAC enforcement, prompt injection detection, PII redaction, and audit logging. Each layer can short-circuit the request with a policy refusal.

## Quick Start

```bash
# Backend
cd app/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python3 -m app

# Frontend (separate terminal)
cd app/frontend
npm install && npm run dev
# Visit http://localhost:5173
```

One-command demo (auto-selects Ollama if available, otherwise stub):
```bash
make demo-local
```

## Core API

| Endpoint | Description |
|---|---|
| `POST /auth/login` | Issue JWT (local_jwt or OIDC mode) |
| `POST /uc1/architecture` | LLM-assisted architecture query (RBAC-gated RAG) |
| `POST /uc2/log-intel` | Log intelligence and root cause generation |
| `GET /audit/summary` | Governance and audit log summary |
| `GET /metrics` | Prometheus metrics (requests, latency, tokens, cost, policy events) |
| `GET /health` | Runtime posture and diagnostics |

## Snowflake / Databricks Integration

**Snowflake** — set `SNOWFLAKE_ACCOUNT` to activate. Stores eval results and audit logs; supports `query_eval_history()`, `query_audit_history()`, aggregate reporting.

**Databricks** — set `DATABRICKS_HOST` to activate. MLflow experiment tracking per eval run; Delta audit tables in Unity Catalog; `databricks-cli` or service-principal OAuth auth.

## Deployment

**Docker**
```bash
cd infra && docker-compose up --build
```

**Kubernetes**
```bash
kubectl create namespace llm-adoption
kubectl apply -f infra/k8s/secret.yaml
kubectl apply -f infra/k8s/
```

**CI/CD** — GHCR Docker image published on every push to `main`. Security scan (pip-audit, bandit, Trivy) runs on schedule.

## Tech Stack

Python · FastAPI · React · Vite · Chroma · SQLite · Snowflake · Databricks (MLflow, Delta Lake) · AWS Bedrock · Kubernetes · Terraform · Prometheus · Grafana · OpenTelemetry

## Related Projects

For governed NL-to-SQL analytics, see [Nexus-Hive](https://github.com/KIM3310/Nexus-Hive). For the data pipeline layer, see [lakehouse-contract-lab](https://github.com/KIM3310/lakehouse-contract-lab).

## License

MIT
