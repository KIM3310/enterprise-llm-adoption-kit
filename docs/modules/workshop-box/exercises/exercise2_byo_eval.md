# Exercise 2 — BYO Evals

- Validate a sample dataset
- Run eval on a subset and inspect the report

Commands:
```bash
python3 evals/runner/dataset_ingest.py --input evals/datasets/sample_dataset.csv
python3 evals/runner/run_eval.py --dataset evals/datasets/initial_20.jsonl
```
