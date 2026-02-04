# Module — Red Team & Safety Eval Pack

Goal: safety-focused dataset + guardrails + eval gate evidence.

## Run
```bash
python3 evals/runner/run_eval.py --dataset evals/datasets/redteam_50.jsonl
python3 evals/runner/create_baseline.py --dataset evals/datasets/redteam_50.jsonl --output evals/reports/redteam_baseline.json
python3 evals/runner/eval_gate.py --report evals/reports/latest_report.json --baseline evals/reports/redteam_baseline.json
```

Artifacts live in `evals/reports/`.
