# Changelog

All notable changes to the Enterprise LLM Adoption Kit are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-10

### Added
- RBAC enforcement at retrieval time with Employee, Ops, and Admin role gates
- Prompt injection detection using keyword heuristics with matched-pattern logging
- PII redaction with enterprise-mode SHA-256 hashing for emails, phone numbers, and identifiers
- RAG retrieval pipeline with Chroma vector store and deterministic hash embeddings
- Evals harness with baseline diffs, report generation, and red-team dataset support
- LLMOps metrics exported via Prometheus (latency, tokens, cost, policy events)
- Snowflake integration for eval result persistence and audit log storage (env-var gated)
- Databricks integration with MLflow experiment tracking and Delta audit tables in Unity Catalog (env-var gated)
- AWS Bedrock runtime mode alongside stub, OpenAI, and Ollama providers
- Kubernetes deployment manifests with HPA auto-scaling, TLS ingress, and AlertManager rules
- FastAPI backend with JWT/OIDC authentication and structured audit logging
- React + Vite frontend with executive summary dashboard and service brief board
- Docker Compose and multi-cloud Terraform configurations (AWS, GCP)
- CI/CD pipelines: quality gate, security scan, Docker publish, production smoke tests
