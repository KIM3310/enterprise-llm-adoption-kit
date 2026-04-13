# ADR-001: Layered Governance Pipeline with Independent Short-Circuit Layers

**Status:** Accepted
**Date:** 2026-01-15
**Author:** Doeon Kim

## Context

Enterprise LLM deployments require governance controls that prevent unsafe, unauthorized, or policy-violating interactions before they reach the LLM provider. The question is whether to implement these controls as a single monolithic middleware, or as independent, composable layers.

Common approaches in the industry include:

1. **Single guardrail function** -- one middleware that checks auth, content policy, PII, and injection in a combined pass. Simpler to implement but harder to test, audit, and extend.
2. **External guardrail service** -- a separate microservice (e.g., NVIDIA NeMo Guardrails, Guardrails AI) that handles all policy checks. Adds network latency and operational complexity.
3. **Layered pipeline with independent modules** -- each governance concern is a separate module with its own test surface, failure mode, and audit trail. Layers are composed in a fixed order and each can short-circuit the request.

## Decision

We chose option 3: a four-layer governance pipeline where each layer is an independent Python module with its own test file:

| Layer | Module | Responsibility |
|---|---|---|
| 1. RBAC | `rbac.py` | Map authenticated roles to document-access groups |
| 2. Injection Detection | `injection.py` | Flag known prompt-injection patterns |
| 3. PII Redaction | `redaction.py` | Mask emails, phone numbers, and identifiers |
| 4. Safety Policy | `safety.py` | Enforce 22 content-policy regex patterns |

Each layer:
- Receives the request context and can return a policy refusal immediately.
- Produces structured policy events (e.g., `injection_detected`, `pii_redacted`, `safety_refused`) that are recorded in the audit log.
- Is independently unit-testable without standing up the full application.
- Has no dependency on the other governance layers -- they compose via sequential execution in `main.py`.

## Rationale

### Independent testability
Each governance module has its own test file (`test_rbac.py`, `test_injection.py`, `test_redaction.py`, `test_safety_guardrails.py`). This allows targeted regression testing when modifying a single policy dimension without running the full integration suite.

### Audit granularity
Because each layer produces its own policy events, the audit log records exactly which governance layer triggered a refusal. This is critical for enterprise compliance reviews where auditors need to know whether a request was blocked for access control reasons vs. content policy reasons.

### Short-circuit efficiency
The layers execute in a fixed order (RBAC -> Injection -> PII -> Safety). If RBAC denies access, the request never reaches injection detection, avoiding unnecessary computation. This also means a request that passes all four layers has a complete attestation chain.

### Extensibility
Adding a new governance dimension (e.g., toxicity scoring, cost-budget enforcement) requires only adding a new module and inserting it into the pipeline sequence. No existing modules need modification.

### ReDoS protection
The safety module (`safety.py`) uses bounded wildcards (`.{0,200}`) instead of unbounded `.*` in all regex patterns, and truncates input to `_MAX_SCAN_LENGTH = 10_000` characters before scanning. This prevents catastrophic backtracking attacks that could DoS the governance layer itself.

## Alternatives Considered

### Single guardrail function
- Pro: fewer files, simpler initial implementation.
- Con: testing one concern requires mocking or ignoring the others. Policy refusal audit events would be ambiguous about which check triggered the refusal. Modifying PII patterns risks breaking injection detection.

### External guardrail microservice
- Pro: language-agnostic, can be shared across multiple LLM applications.
- Con: adds network round-trip latency to every request. Requires separate deployment, monitoring, and scaling. For a single-application governance kit, the operational overhead outweighs the reuse benefit.

### LLM-based content moderation (e.g., calling a moderation endpoint)
- Pro: catches nuanced policy violations that regex cannot.
- Con: adds LLM inference cost and latency to the governance layer itself. Creates a circular dependency where the governance system depends on LLM availability. Regex-based patterns provide deterministic, auditable, zero-cost-per-request enforcement.

## Consequences

- Every request incurs four sequential module calls, but each is sub-millisecond (regex matching and set lookups).
- Adding a new governance layer requires updating the pipeline composition in `main.py`.
- The regex-based approach will not catch sophisticated adversarial inputs that evade pattern matching. This is a known limitation documented in the eval red-team datasets.
- Enterprise audit requirements are satisfied because each policy decision is individually logged with its trigger category.
