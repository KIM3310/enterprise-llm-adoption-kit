import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "evals" / "datasets" / "ingested"

REQUIRED_FIELDS = {"id", "use_case", "input", "role", "sensitivity"}
ALLOWED_USE_CASES = {"uc1", "uc2"}
ALLOWED_ROLES = {"Employee", "Ops", "Admin"}


def load_records(path: Path) -> List[dict]:
    records: List[dict] = []
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    elif path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    else:
        raise ValueError("Unsupported file type. Use CSV or JSONL.")
    return records


def validate_records(records: List[dict]) -> List[str]:
    errors: List[str] = []
    for idx, record in enumerate(records, 1):
        missing = REQUIRED_FIELDS - set(record.keys())
        if missing:
            errors.append(f"Row {idx}: missing fields {sorted(missing)}")
            continue
        if record.get("use_case") not in ALLOWED_USE_CASES:
            errors.append(f"Row {idx}: invalid use_case {record.get('use_case')}")
        if record.get("role") not in ALLOWED_ROLES:
            errors.append(f"Row {idx}: invalid role {record.get('role')}")
        if not record.get("input"):
            errors.append(f"Row {idx}: input is empty")
    return errors


def _suggestions() -> List[dict]:
    suggestions = []
    uc1_templates = [
        "Summarize handover risks for payments prod",
        "List runbook steps for identity staging",
        "Provide handover summary for analytics prod",
        "Highlight dependencies for inventory dev",
        "Summarize handover notes for notifications prod",
    ]
    uc2_templates = [
        "ERROR Timeout while calling payments API",
        "Build failed: Connection refused to redis",
        "OutOfMemoryError in worker",
        "Permission denied writing to /var/log",
        "Deployment error 502 Server Error",
    ]
    for i, prompt in enumerate(uc1_templates, 1):
        suggestions.append(
            {
                "id": f"auto-uc1-{i:02d}",
                "use_case": "uc1",
                "input": prompt,
                "expected": "",
                "role": "Employee",
                "sensitivity": "low",
                "tags": ["auto_suggested"],
            }
        )
    for i, prompt in enumerate(uc2_templates, 1):
        suggestions.append(
            {
                "id": f"auto-uc2-{i:02d}",
                "use_case": "uc2",
                "input": prompt,
                "expected": "",
                "role": "Ops",
                "sensitivity": "medium",
                "tags": ["auto_suggested"],
            }
        )
    return suggestions


def enrich_records(records: List[dict]) -> Tuple[List[dict], bool]:
    if len(records) >= 10:
        return records, False
    augmented = records + _suggestions()
    return augmented, True


def write_output(records: List[dict], source_name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{ts}_{source_name}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    records = load_records(input_path)
    errors = validate_records(records)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    final_records, augmented = enrich_records(records)
    out_path = write_output(final_records, input_path.stem)

    print(f"Records ingested: {len(records)}")
    if augmented:
        print("Dataset too small; added 10 suggested test cases")
    print(f"Output written: {out_path}")


if __name__ == "__main__":
    main()
