import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_kr_dataset_schema():
    path = ROOT_DIR / "evals/datasets/kr_enterprise_30.jsonl"
    assert path.exists()
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 30
    for line in lines:
        record = json.loads(line)
        for key in ["id", "use_case", "input", "role", "sensitivity"]:
            assert key in record
