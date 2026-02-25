from app.audit import log_audit


def test_log_audit_forwards_hash_payload_to_databricks(monkeypatch) -> None:
    calls = {}

    def fake_store_audit_event_delta(**kwargs):  # type: ignore[no-untyped-def]
        calls.update(kwargs)

    monkeypatch.setattr("app.audit.store_audit_event_delta", fake_store_audit_event_delta)

    log_audit(
        {
            "request_id": "req-456",
            "user_id": "demo-user",
            "roles": ["Admin"],
            "use_case": "uc2",
            "model_config": {"provider": "stub"},
            "payload_redacted": {
                "input_hash": "in-hash",
                "output_hash": "out-hash",
                "mode": "enterprise",
            },
            "policy_events": {"refusal": False},
            "tokens_in": 12,
            "tokens_out": 21,
        }
    )

    assert calls["event_id"] == "req-456"
    assert calls["event_type"] == "uc2"
    assert calls["user_id"] == "demo-user"
    assert calls["role"] == "Admin"
    assert calls["input_hash"] == "in-hash"
    assert calls["output_hash"] == "out-hash"
    assert calls["mode"] == "enterprise"
    assert calls["metadata"]["request_id"] == "req-456"
