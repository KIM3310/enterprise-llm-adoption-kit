import json
from pathlib import Path


def test_sample_audit_schema():
    path = Path("/Users/s/enterprise-llm-adoption-kit/app/backend/data/sample_audit.json")
    assert path.exists()
    data = json.loads(path.read_text())

    required = [
        "request_id",
        "timestamp",
        "user_id",
        "roles",
        "use_case",
        "model_config",
        "retrieval_doc_ids",
        "tool_calls",
        "latency_ms",
        "tokens_in",
        "tokens_out",
        "cost_estimate",
        "policy_events",
    ]
    for key in required:
        assert key in data

    assert isinstance(data["roles"], list)
    assert isinstance(data["model_config"], dict)
    assert isinstance(data["retrieval_doc_ids"], list)
    assert isinstance(data["tool_calls"], list)
    assert isinstance(data["policy_events"], list)

    if data["retrieval_doc_ids"]:
        first = data["retrieval_doc_ids"][0]
        assert "doc_id" in first
        assert "field_path" in first
