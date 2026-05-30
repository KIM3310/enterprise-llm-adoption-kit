# Enterprise LLM Adoption Kit

[![CI](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/ci.yml)
[![Security Scan](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/security-scan.yml)
[![Docker](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/KIM3310/enterprise-llm-adoption-kit/actions/workflows/docker-publish.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Production-grade governance toolkit for enterprise LLM deployments** -- RBAC, prompt-injection detection, PII redaction, audit logging, eval harness, and multi-cloud LLM routing, all wired into a single FastAPI + React application with Kubernetes-ready infrastructure.

> All rollout data and review scenarios are synthetic. The goal is a reviewable, runnable validation kit that demonstrates enterprise-grade LLM governance patterns end to end.

Technical review pack: [`docs/technical-review-pack.md`](docs/technical-review-pack.md)

Demo video: [https://youtu.be/yMq03b0js0E](https://youtu.be/yMq03b0js0E)

---

## Product and Review Surface

| Lens | Current answer |
|---|---|
| Buyer or user | Enterprise AI adoption, IT governance, security, platform, and operations teams that need controlled LLM rollout. |
| Commercial route | Paid adoption workshop, governance template pack, implementation starter, and optional observability/data-platform integration. |
| Review signal | RBAC, prompt-injection checks, PII redaction, audit logs, eval gates, Snowflake/Databricks adapters, and deployment scaffolding in one runnable kit. |
| Safety boundary | Synthetic rollout scenarios by default; external providers and enterprise data adapters are environment-gated. |
| Fast proof | `make verify`, [`docs/technical-review-pack.md`](docs/technical-review-pack.md), and [`docs/sales/poc_success_criteria.md`](docs/sales/poc_success_criteria.md). |

## Reviewer Fast Path

- **First minute:** Open the governance layers, eval gate, and PoC success criteria before the full architecture.
- **Local demo:** Run the backend and frontend quick-start commands, then open `http://localhost:8000` and `http://localhost:5173`.
- **Verification:** Run `make verify`; it covers backend quality, smoke checks, and frontend build.
- **Commercial read:** Sell it as an enterprise LLM adoption workshop and governance starter kit.

---

## Commercialization Playbook

- [Monetization and GTM playbook](docs/monetization-playbook.md) maps the repository to buyer segments, offer ladder, pricing hypotheses, proof gates, and risk boundaries.

## Review Notes

- [Review guide](docs/reviewer-evidence-map.md) summarizes the project angle, first files to inspect, verification commands, and known boundaries.
- [Quality notes](docs/quality-gate.md) lists the local checks, CI surface, and release expectations for this repository.
- [Revenue growth model](docs/revenue-growth-model.md) maps the project to an ethical revenue path, activation loop, pricing logic, and growth experiments.
- [Enterprise readiness notes](docs/enterprise-readiness.md) outlines security, data, operations, integration, and handoff expectations.
- [Conversion UX model](docs/conversion-ux-model.md) maps the buyer path, behavioral design, UI/UX direction, pricing frame, and ethical conversion guardrails.

## Architecture

Every request passes through four governance layers before reaching the LLM. Each layer can short-circuit the request with a policy refusal, and every decision is audit-logged.

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI["React + Vite UI"]
        CLI["API / CLI Consumer"]
    end

    subgraph Gateway["API Gateway"]
        ING["TLS Ingress"] --> AUTH["JWT / OIDC Auth"]
        AUTH --> RL["Rate Limiter"]
    end

    subgraph Governance["Governance Pipeline -- 4 Layers"]
        direction TB
        RBAC["1. RBAC Enforcement<br/><i>Employee / Ops / Admin</i>"]
        INJ["2. Prompt Injection Detection<br/><i>keyword + regex heuristics</i>"]
        PII["3. PII Redaction<br/><i>email, phone, ID masking</i>"]
        SAFE["4. Safety Policy Engine<br/><i>22 regex patterns, ReDoS-safe</i>"]
        RBAC --> INJ --> PII --> SAFE
    end

    subgraph Core["Application Core"]
        RAG["RAG Retrieval<br/><i>ChromaDB + hash embeddings</i>"]
        LLM["LLM Router<br/><i>OpenAI / Ollama / Bedrock / Stub</i>"]
        TOOLS["Tool Executor<br/><i>allowlisted tools only</i>"]
        RAG --> LLM
        LLM --> TOOLS
    end

    subgraph Observability["Observability + Persistence"]
        AUDIT["Audit Logger<br/><i>SHA-256 enterprise hashing</i>"]
        PROM["Prometheus Metrics<br/><i>latency, tokens, cost, policy</i>"]
        OTEL["OpenTelemetry<br/><i>OTLP traces</i>"]
        DD["Datadog Integration"]
    end

    subgraph DataPlatform["Data Platform Integration"]
        SF["Snowflake<br/><i>eval + audit persistence</i>"]
        DB["Databricks<br/><i>MLflow + Delta Lake</i>"]
        EVAL["Eval Harness<br/><i>baseline diffs, red-team</i>"]
    end

    UI & CLI --> ING
    RL --> RBAC
    SAFE --> RAG
    LLM --> AUDIT & PROM & OTEL
    AUDIT --> SF & DB
    OTEL --> DD
    EVAL --> SF & DB

    style Governance fill:#fff3e0,stroke:#e65100
    style Observability fill:#e8f5e9,stroke:#2e7d32
    style DataPlatform fill:#e3f2fd,stroke:#1565c0
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend API** | Python 3.11+, FastAPI, Uvicorn, Pydantic |
| **Frontend** | React 18, Vite |
| **Auth** | JWT (HS256) with key rotation, OIDC (RS256) via JWKS discovery |
| **RAG** | ChromaDB, deterministic hash embeddings, in-memory fallback |
| **LLM Providers** | OpenAI, Ollama, AWS Bedrock, stub (offline deterministic) |
| **Eval** | Custom harness -- accuracy, groundedness, helpfulness, safety scoring |
| **Storage** | SQLite, Chroma, JSONL event logs |
| **Data Platform** | Snowflake (eval + audit), Databricks (MLflow + Delta Lake) |
| **Observability** | Prometheus, Grafana, OpenTelemetry (OTLP), Datadog-ready |
| **Infrastructure** | Docker Compose, Kubernetes (HPA, TLS ingress, AlertManager), Terraform (AWS + GCP) |
| **CI/CD** | GitHub Actions (CI, security scan, Docker publish, Cloudflare Pages deploy) |
| **Security** | pip-audit, Bandit, Trivy container scanning |

---

## Quick Start

### One-command demo (recommended)

```bash
git clone https://github.com/KIM3310/enterprise-llm-adoption-kit.git
cd enterprise-llm-adoption-kit
make demo-local        # auto-selects Ollama if available, otherwise stub
```

### Manual setup

```bash
# 1. Backend
cd app/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python3 -m app                    # starts on http://localhost:8000

# 2. Frontend (separate terminal)
cd app/frontend
npm install && npm run dev        # starts on http://localhost:5173

# 3. Verify everything
make verify                       # syntax, deps, pytest, smoke, frontend build
```

### Docker

```bash
cd infra && docker-compose up --build
# Backend: http://localhost:8000   Frontend: http://localhost:5173
```

### Kubernetes

```bash
kubectl create namespace llm-adoption
kubectl apply -f infra/k8s/secret.yaml
kubectl apply -f infra/k8s/
```

---

## Key Capabilities

| Capability | Description | Code |
|---|---|---|
| **RBAC** | Role-to-access-group mapping enforced at RAG retrieval time (Employee / Ops / Admin) | [`app/backend/app/rbac.py`](app/backend/app/rbac.py) |
| **Prompt Injection Detection** | Keyword heuristics flag known injection patterns before LLM invocation | [`app/backend/app/injection.py`](app/backend/app/injection.py) |
| **Safety Policy Engine** | 22 regex patterns targeting exfiltration, escalation, and adversarial prompts (ReDoS-safe) | [`app/backend/app/safety.py`](app/backend/app/safety.py) |
| **PII Redaction** | Email, phone, and ID masking with per-category event tracking | [`app/backend/app/redaction.py`](app/backend/app/redaction.py) |
| **Audit Logging** | Structured JSON logs with SHA-256 hashing in enterprise mode and auto-retention pruning | [`app/backend/app/audit.py`](app/backend/app/audit.py) |
| **RAG Retrieval** | ChromaDB + deterministic hash embeddings with RBAC-filtered document access | [`app/backend/app/rag.py`](app/backend/app/rag.py) |
| **Eval Harness** | Accuracy, groundedness, helpfulness, safety scoring with baseline diffs and red-team datasets | [`evals/runner/`](evals/runner/) |
| **LLMOps Metrics** | Request latency, token counts, cost tracking, policy events via Prometheus | [`app/backend/app/metrics.py`](app/backend/app/metrics.py) |
| **Circuit Breaker** | LLM provider failure isolation with configurable threshold and cooldown | [`app/backend/app/llm_adapter.py`](app/backend/app/llm_adapter.py) |
| **Multi-provider LLM** | Hot-swappable runtime config across OpenAI, Ollama, Bedrock, and stub backends | [`app/backend/app/llm_adapter.py`](app/backend/app/llm_adapter.py) |
| **Snowflake Integration** | Eval results and audit logs persisted to Snowflake (env-var gated) | [`app/backend/app/snowflake_adapter.py`](app/backend/app/snowflake_adapter.py) |
| **Databricks Integration** | MLflow experiment tracking and Delta audit tables in Unity Catalog | [`app/backend/app/databricks_adapter.py`](app/backend/app/databricks_adapter.py) |
| **OpenTelemetry** | OTLP trace export with Datadog-ready integration | [`app/backend/app/telemetry.py`](app/backend/app/telemetry.py) |

---

## Core API

| Endpoint | Description |
|---|---|
| `POST /auth/login` | Issue JWT (local_jwt or OIDC mode) |
| `POST /uc1/architecture` | LLM-assisted architecture query (RBAC-gated RAG) |
| `POST /uc2/log-intel` | Log intelligence and root cause generation |
| `GET /audit/summary` | Governance and audit log summary |
| `GET /metrics` | Prometheus metrics (requests, latency, tokens, cost, policy events) |
| `GET /health` | Runtime posture and diagnostics |
| `GET /ops/service-brief` | Operational service brief and readiness summary |
| `GET /ops/resource-pack` | Resource pack for review and evidence |

---

## Snowflake / Databricks Integration

**Snowflake** -- set `SNOWFLAKE_ACCOUNT` to activate. Stores eval results and audit logs; supports `query_eval_history()`, `query_audit_history()`, aggregate reporting.

**Databricks** -- set `DATABRICKS_HOST` to activate. MLflow experiment tracking per eval run; Delta audit tables in Unity Catalog; `databricks-cli` or service-principal OAuth auth.

See [`.env.example`](.env.example) for the full configuration surface.

---

## Datadog-Ready Pack

- Datadog-ready resource pack: [`docs/datadog/README.md`](docs/datadog/README.md)
- Existing env hooks already reserve a Datadog integration lane in `.env.example`
- Current state: asset sync and OTLP wiring are prepared, but live tenant integration is intentionally disabled by default
- Best use: show how enterprise LLM governance, audit, latency, and rollout readiness would be observed in one operator-facing Datadog surface

---

## Project Structure

```
enterprise-llm-adoption-kit/
  app/
    backend/               # FastAPI backend (RBAC, RAG, safety, audit, LLM adapters)
      app/
        main.py            # FastAPI app with governance middleware
        rbac.py            # Role-to-access-group mapping
        safety.py          # 22-pattern safety policy engine
        injection.py       # Prompt injection detection
        redaction.py       # PII redaction engine
        audit.py           # Structured audit logging with SHA-256 hashing
        auth.py            # JWT/OIDC authentication
        llm_adapter.py     # Multi-provider LLM router with circuit breaker
        rag.py             # ChromaDB RAG with RBAC-filtered retrieval
        snowflake_adapter.py
        databricks_adapter.py
        metrics.py         # Prometheus metric definitions
        telemetry.py       # OpenTelemetry instrumentation
        config.py          # 60+ env vars, type-safe parsing
    frontend/              # React + Vite UI
  evals/
    runner/                # Eval harness (run_eval, eval_gate, baseline)
    datasets/              # Test datasets (initial, red-team, Korean)
    reports/               # Generated eval reports and diffs
  infra/
    k8s/                   # Kubernetes manifests (HPA, TLS, AlertManager)
    aws/terraform/         # AWS ECS + ALB Terraform module
    gcp/terraform/         # GCP Terraform module
    docker-compose.yml     # Local multi-service orchestration
    monitoring/            # Grafana dashboard + AlertManager rules
  tests/                   # 30+ test files, 84% backend coverage
  docs/                    # Architecture, ops, blueprint, Datadog, evals docs
  scripts/                 # Demo runners, quality gates, release ops
```

---

## Technical Proof Boundary

- **Primary architecture lane:** enterprise LLM governance, applied AI controls, and platform integration
- **Strongest proof surface:** governance pipeline, eval harness, observability surfaces, and deployment-ready backend/frontend split
- **What is real here:** RBAC, safety pipeline, audit logging, metrics, integration adapters, CI/CD, and deployment scaffolding
- **What is bounded here:** review cases and documents are synthetic, and Snowflake / Databricks / Bedrock integrations are env-gated

---

## Latest Verified Snapshot

- **Verified on:** 2026-04-07
- **Command:** `make verify`
- **Outcome:** passed locally; syntax check, dependency check, pytest, smoke diagnostics, and frontend production build completed with 84.20% backend coverage
- **Notes:** `make verify` bootstraps the Python 3.11 backend venv and installs missing frontend dependencies automatically, and Snowflake adapter plus Snowflake-focused service-brief tests were rerun successfully from `app/backend/.venv`

---

## CI/CD

GHCR Docker image published on every push to `main`. Security scan (pip-audit, bandit, Trivy) runs on schedule. Frontend auto-deploys to Cloudflare Pages.

---

## Related Projects

For governed NL-to-SQL analytics, see [Nexus-Hive](https://github.com/KIM3310/Nexus-Hive). For the data pipeline layer, see [lakehouse-contract-lab](https://github.com/KIM3310/lakehouse-contract-lab).

## License

MIT

## Cloud + AI Architecture

This repository includes a neutral cloud and AI engineering blueprint that maps the current proof surface to runtime boundaries, data contracts, model-risk controls, deployment posture, and validation hooks.

- [Cloud + AI architecture blueprint](docs/cloud-ai-architecture.md)
- [Machine-readable architecture manifest](docs/architecture/blueprint.json)
- Validation command: `python3 scripts/validate_architecture_blueprint.py`
