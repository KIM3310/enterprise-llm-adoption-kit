# Bring Your Own Dataset (BYO)

## Accepted Formats
- CSV or JSONL

## Required Columns
- id, use_case, input, role, sensitivity
- expected is optional

## Usage
```
python3 evals/runner/dataset_ingest.py --input /path/to/dataset.csv
```

## Behavior
- Validates schema and basic fields
- If dataset has fewer than 10 rows, auto-adds 10 suggested test cases
- Writes output to `evals/datasets/ingested/<timestamp>_<source>.jsonl`

