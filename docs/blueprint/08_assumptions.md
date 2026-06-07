# Assumptions

1) Local development environment is sufficient for demo (no real cloud services).
2) Mock JWT auth is acceptable for technical review demo; real OIDC/SAML integration is documented but not implemented.
3) Synthetic handover docs are acceptable for demonstrating RAG pipeline.
4) Deterministic stub LLM is acceptable for offline evaluation; adapter enables LLM integration later.
5) PII redaction uses baseline regex and is not a full DLP system.
6) Evaluation scoring can be heuristic or manual; rubric defines expected review process.
7) The UI is minimal by design to prioritize security, evals, and observability.
8) Role model is limited to Employee/Ops/Admin for demo scope.
9) Costs are estimated using heuristic token scope; not authoritative.

