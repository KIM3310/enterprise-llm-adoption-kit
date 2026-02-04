import json
from pathlib import Path


def test_kr_dataset_schema():
    path = Path("/Users/s/enterprise-llm-adoption-kit/evals/datasets/kr_enterprise_30.jsonl")
    assert path.exists()
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 30
    for line in lines:
        record = json.loads(line)
        for key in ["id", "use_case", "input", "role", "sensitivity"]:
            assert key in record
