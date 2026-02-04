# Evals Plan

## Goals
- Provide repeatable, regression-friendly evaluation of UC1/UC2
- Enable baseline comparison for model/prompt changes
- Produce Markdown + JSON reports

## Dataset Plan
- **Format**: JSONL with fields:
  - id, use_case, input, expected (optional), tags, sensitivity, role
- **Initial 20Q set**: 10 UC1 + 10 UC2 (human-style prompts)
- **Starter 50-case set**: 25 UC1 + 25 UC2
- **Korean set**: initial_20_ko.jsonl (10 UC1 + 10 UC2)
- **Synthetic docs**: ~70 handover docs normalized into JSON schema

## Rubric (1-5)
- **Accuracy**: correct facts/steps
- **Groundedness**: citations map to retrieved doc_id + field paths
- **Helpfulness**: actionable, complete response
- **Safety**: no unsafe actions or data leakage; respects redaction and RBAC

## Evaluation Process
1) Load dataset JSONL
2) Call backend endpoint for each sample
3) Capture output, citations, tool calls, policy events
4) Score each dimension (manual rubric or heuristic placeholder)
5) Generate report.json and report.md
6) Compare against baseline to produce diff report

## Reporting Artifacts
- `evals/reports/latest_report.json`
- `evals/reports/latest_report.md`
- `evals/reports/baseline_diff.md`

## Future Enhancements
- Add human-in-the-loop scoring UI
- Expand rubric with fluency/consistency
