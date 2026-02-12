import json

from app.audit_viewer import summarize_log


def _event(user_id: str, cost: float) -> str:
    return json.dumps(
        {
            "user_id": user_id,
            "cost_estimate": cost,
            "tool_calls": [{"name": "runbook_lookup"}],
            "policy_events": {"refusal": True},
        }
    )


def test_summarize_log_respects_max_lines(tmp_path) -> None:
    audit_log = tmp_path / "audit.log"
    audit_log.write_text(
        "\n".join([
            _event("user-a", 1.0),
            _event("user-b", 2.0),
            _event("user-b", 3.0),
        ]),
        encoding="utf-8",
    )

    summary = summarize_log(audit_log, max_lines=2)

    assert summary["requests"] == 2
    assert summary["top_users"][0] == ("user-b", 2)
    assert summary["total_cost"] == 5.0


def test_summarize_log_ignores_non_utf8_bytes(tmp_path) -> None:
    audit_log = tmp_path / "audit.log"
    with audit_log.open("wb") as handle:
        handle.write(_event("user-a", 1.1).encode("utf-8"))
        handle.write(b"\n\xff\xfe\xfa\n")

    summary = summarize_log(audit_log, max_lines=50)

    assert summary["requests"] == 1
    assert summary["total_cost"] == 1.1
