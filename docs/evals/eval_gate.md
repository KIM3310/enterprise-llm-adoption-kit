# Eval Gate

## Purpose
Fail the build if safety/groundedness fall below thresholds or if regressions exceed a max drop.

## Usage
```
python3 evals/runner/eval_gate.py \
  --report evals/reports/latest_report.json \
  --baseline evals/reports/baseline_report.json \
  --min-safety 3.5 \
  --min-groundedness 3.0 \
  --max-regression-drop 0.3
```

## Output
- Writes `evals/reports/gate_diff.md` with top 10 regressions and examples

