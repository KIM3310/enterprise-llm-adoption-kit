# Architecture

## High-Level Component Diagram (ASCII)

```
+------------------------------+            +---------------------------+
|   User Browser (React UI)    |            |     CLI Eval Runner       |
| - Login / UC1 / UC2          |            | - Dataset JSONL           |
+---------------+--------------+            +-------------+-------------+
                | HTTPS                                 |
                v                                       v
+---------------+---------------------------------------+--------------+
|                         FastAPI Backend                               |
|  - Auth (JWT)            - RBAC Policy Engine                         |
|  - Use Case Orchestrator - Prompt Assembly (context separation)       |
|  - PII Redaction         - Injection Detector                         |
|  - Tool Router (allowlist)                                            |
|  - Audit Logger (JSON file + stdout)                                  |
|  - Metrics (/metrics) + Rate Limiter                                  |
|  - LLM Adapter (stub/local or provider via ENV)                        |
+---------------+--------------------+------------------+--------------+
                |                    |                  |
                |                    |                  |
                v                    v                  v
     +------------------+   +-------------------+   +------------------+
     | Vector Store     |   | SQLite / Files    |   | Runbook Store    |
     | (Chroma/FAISS)   |   | (requests, docs)  |   | (local JSON)     |
     +------------------+   +-------------------+   +------------------+
                |
                | (optional) external provider
                v
     +---------------------------+
     | LLM Provider (pluggable)  |
     | - LLM via adapter      |
     +---------------------------+
```

## Trust Boundaries
1) **User Device Boundary**: Browser UI -> Backend API
2) **Service Boundary**: Backend internal modules and policy enforcement
3) **Data Boundary**: Vector store + SQLite + file storage (local dev)
4) **External Provider Boundary**: LLM provider (pluggable, optional)

## Key Data Flows
1) **Login** -> Issue JWT (role claim)
2) **UC1 RAG**
   - Input -> PII redaction -> role-filtered retrieval -> prompt assembly -> LLM adapter
   - Output -> PII redaction -> citations appended -> audit log
3) **UC2 Log Intelligence**
   - Input logs -> PII redaction -> tool router (allowlist) -> LLM adapter -> audit log
4) **Evals**
   - Runner loads datasets -> calls backend endpoints -> stores report + diff

## Core Architectural Decisions
- **FastAPI** for explicit API contracts and testability
- **Local vector DB** (Chroma or FAISS) for RAG with metadata filters
- **Pluggable LLM adapter** with deterministic stub default
- **JSON-structured audit logs** for compliance and analytics
- **Minimal React UI** (Vite) for focused demonstration

## Security & Controls Placement
- **RBAC filter** applied at retrieval stage before embedding results
- **PII redaction** applied both pre-LLM and post-LLM
- **Prompt injection detector** and **tool allowlist** enforced before tool calls
- **Citation-only mode** to prevent sensitive content exposure

## Scaling Considerations (Future)
- Swap local storage for cloud equivalents via interfaces
- Replace mock JWT with OIDC/SAML integration
- Replace local vector DB with managed vector service
- Replace stub LLM with LLM provider

