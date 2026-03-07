import json
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_viewer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_audit_viewer_summary():
    events = [
        {
            "user_id": "u1",
            "cost_estimate": 0.1,
            "tool_calls": [{"name": "runbook_lookup"}],
            "policy_events": {"redaction_applied": True},
        },
        {
            "user_id": "u2",
            "cost_estimate": 0.2,
            "tool_calls": [{"name": "knowledge_search"}],
            "policy_events": {"injection_detected": True},
        },
    ]
    lines = [json.dumps(e) for e in events]
    module = _load_module(ROOT_DIR / "app/backend/scripts/audit_viewer.py")
    summary = module.summarize_events(lines)

    assert summary["requests"] == 2
    assert summary["total_cost"] == 0.3
    assert summary["top_users"][0][0] in {"u1", "u2"}
    assert ("runbook_lookup", 1) in summary["tools_used"]
    assert ("redaction_applied", 1) in summary["policy_events"]
