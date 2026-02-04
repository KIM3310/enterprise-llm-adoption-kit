# Demo Script (Executive, 3 min)

## Objective
Show enterprise safety, RBAC, and readiness in under 3 minutes.

## Flow
1) **Positioning (20s)**
   - "This kit demonstrates secure LLM adoption for Applied AI in Korea."
   - "Two deep use cases: Handover Copilot and DevOps Log Intelligence."

2) **Security Controls (45s)**
   - Login as Ops and highlight RBAC
   - Show audit log fields and PII redaction
   - Mention prompt injection defense and tool allowlist

3) **UC1: Handover Copilot (45s)**
   - Ask: "Summarize handover risks for payments prod"
   - Show citations with doc_id + field path
   - Toggle citation-only mode to demonstrate safety

4) **UC2: Log Intelligence (45s)**
   - Paste error logs
   - Show summary + runbook steps
   - Show tool calls (allowlist only)

5) **Metrics + Eval (25s)**
   - Open `/metrics` (counters + latency histogram + policy events)
   - Run eval runner and show `evals/reports/latest_report.md`

6) **Close (20s)**
   - "Ready to connect to LLM via adapter"
   - "Evals and LLMOps are built in for safe scale"
