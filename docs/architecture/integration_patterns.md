# Integration Patterns (Enterprise LLM)

These are common patterns used in enterprise adoption. This doc is guidance only.

## 1) RAG with policy filters
- Retrieve from approved sources
- Apply redaction and injection defenses
- Require citations for sensitive outputs

## 2) Tool calling with allowlists
- Allow only approved tool endpoints
- Log tool inputs/outputs
- Gate tool calls by role

## 3) Human-in-the-loop
- Route uncertain cases to operators
- Record decisions for eval feedback

## 4) Workflow orchestration
- Trigger downstream actions (tickets, alerts)
- Capture audit trail and approvals

## 5) Caching and cost controls
- Cache repeated queries
- Use policy-based routing by user role

References
- Security governance: `docs/architecture/security_governance.md`
- Integration pack: `docs/modules/integration-pack/README.md`
