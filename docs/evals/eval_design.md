# Eval Design

## Dataset Schema
JSONL with fields:
- id, use_case, input, expected(optional), tags, sensitivity, role

## Datasets
- `evals/datasets/initial_20.jsonl`
- `evals/datasets/starter_50.jsonl`
- `evals/datasets/initial_20_ko.jsonl` (Korean prompts)

## Rubric (1-5)
- Accuracy
- Groundedness
- Helpfulness
- Safety

## Reports
- JSON for metrics and raw outputs
- Markdown summary for reviewers
- Baseline diff to catch regressions
