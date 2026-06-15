# Eval Framework Template

Use this template to define how a hypothetical customer could measure LLM performance for a specific use case.

## 1) Use case summary
- Name:
- Primary users:
- Business outcome:
- In-scope tasks:
- Out-of-scope tasks:

## 2) Data and scenarios
- Source systems:
- Data sensitivity tier (public/internal/confidential/restricted):
- Sample size:
- Scenario list (top 10):

## 3) Metrics (define target thresholds)
- Accuracy / task success rate:
- Groundedness / citation rate:
- Safety / refusal correctness:
- Hallucination rate:
- Latency (P95):
- Cost per request:

## 4) Scoring rubric
- Score scale (e.g., 1-5):
- Pass/fail criteria:
- Error taxonomy (policy, retrieval, reasoning, tool, data):

## 5) Guardrails
- Redaction rules:
- Prompt injection handling:
- Tool allowlist:
- Sensitive topics policy:

## 6) Baseline and regression
- Baseline model/version:
- Baseline report:
- Regression gate thresholds:

## 7) Architecture and sign-off
- Stakeholders:
- Architecture cadence:
- Final approval owner:

References
- Eval design: `docs/evals/eval_design.md`
- Eval gate: `docs/evals/eval_gate.md`
- Red-team summary: `docs/evals/redteam_summary.md`
