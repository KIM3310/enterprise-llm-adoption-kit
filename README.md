# Enterprise LLM Adoption Kit

[![CI](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml)
[![Security Scan](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml)
[![Docker](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

End-to-end enterprise LLM adoption kit covering discovery, secure architecture, evals, and LLMOps. All data and rollout scenarios are synthetic — the goal is a reviewable, runnable validation kit.

Demo video: https://youtu.be/yMq03b0js0E

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

## Governance Architecture

Every request passes through four governance layers before reaching the LLM provider. The layers interact as a pipeline where each stage can short-circuit the request with a policy refusal.

```
                           ┌──────────────────────────────────┐
                           │         Ingress (TLS)            │
                           └──────────────┬───────────────────┘
                                          │
                           ┌──────────────▼───────────────────┐
                           │  1. RBAC Enforcement              │
                           │  JWT/OIDC → UserContext → role    │
                           │  gate (Employee / Ops / Admin)    │
                           └──────────────┬───────────────────┘
                                          │ allowed
                           ┌──────────────▼───────────────────┐
                           │  2. Prompt Injection Detection    │
                           │  Keyword heuristics scan input    │
                           │  → flag + matched patterns list   │
                           │  → refusal if injection detected  │
                           └──────────────┬───────────────────┘
                                          │ clean
                           ┌──────────────▼───────────────────┐
                           │  3. PII Redaction                 │
                           │  Regex-based email/phone/ID mask  │
                           │  Enterprise-mode: SHA-256 hashing │
                           │  → redacted payload forwarded     │
                           └──────────────┬───────────────────┘
                                          │ redacted
                           ┌──────────────▼───────────────────┐
                           │  4. LLM Provider + RAG Retrieval  │
                           │  Chroma vector store (RBAC-gated) │
                           │  OpenAI / Ollama / Bedrock / stub │
                           └──────────────┬───────────────────┘
                                          │
                           ┌──────────────▼───────────────────┐
                           │  5. Audit Logging                 │
                           │  Every request → structured log   │
                           │  input_hash + output_hash stored  │
                           │  → Snowflake / Databricks Delta   │
                           │  → Prometheus metrics exported    │
                           └──────────────────────────────────┘
```

RBAC gates retrieval scope so lower-privilege roles never see documents above their clearance. Prompt injection detection runs before any LLM call, preventing adversarial inputs from reaching the model. PII redaction ensures no personally identifiable information is persisted in logs or forwarded to third-party providers. Audit logging captures a tamper-evident record of every interaction, with hashed payloads stored in Snowflake and Databricks Delta tables for compliance review.

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

## Snowflake / Databricks Integration

**Snowflake** — set `SNOWFLAKE_ACCOUNT` to activate. Stores eval results and audit logs; supports `query_eval_history()`, `query_audit_history()`, aggregate reporting.

**Databricks** — set `DATABRICKS_HOST` to activate. MLflow experiment tracking per eval run; Delta audit tables in Unity Catalog; `databricks-cli` or service-principal OAuth auth.

See [`app/backend/app/snowflake_adapter.py`](app/backend/app/snowflake_adapter.py) and [`app/backend/app/databricks_adapter.py`](app/backend/app/databricks_adapter.py).

## Core API

| Endpoint | Description |
|---|---|
| `POST /auth/login` | Issue JWT (local_jwt or OIDC mode) |
| `POST /uc1/architecture` | LLM-assisted architecture query (RBAC-gated RAG) |
| `POST /uc2/log-intel` | Log intelligence and root cause generation |
| `GET /audit/summary` | Governance and audit log summary |
| `GET /metrics` | Prometheus metrics (requests, latency, tokens, cost, policy events) |
| `GET /health` | Runtime posture and diagnostics |

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
kubectl -n llm-adoption get pods,svc,hpa,ingress
```

**CI/CD** — GHCR Docker image published on every push to `main`. Security scan (pip-audit, bandit, Trivy) runs on schedule.

## Tech Stack

Python · FastAPI · React · Vite · Chroma · SQLite · Snowflake · Databricks (MLflow, Delta Lake) · AWS Bedrock · Kubernetes · Terraform · Prometheus · Grafana · OpenTelemetry

## Related Projects

For governed NL-to-SQL analytics, see [Nexus-Hive](https://github.com/KIM3310/Nexus-Hive). For the data pipeline layer, see [lakehouse-contract-lab](https://github.com/KIM3310/lakehouse-contract-lab).

## License

MIT
