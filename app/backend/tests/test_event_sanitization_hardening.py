import app.main as main_module


def test_service_event_context_masks_sensitive_values(monkeypatch) -> None:
    captured = {}

    def _capture(*, level, component, message, context):
        captured["level"] = level
        captured["component"] = component
        captured["message"] = message
        captured["context"] = context

    monkeypatch.setattr(main_module, "record_service_event", _capture)

    main_module._safe_record_service_event(
        level="WARN",
        component="unit-test",
        message="x" * 500,
        context={
            "api_key": "sk-123",
            "authorization": "Bearer very-secret-token",
            "nested": {
                "password": "p@ss",
                "safe_note": "ok",
            },
            "long_text": "A" * 700,
        },
    )

    assert captured["level"] == "WARN"
    assert captured["component"] == "unit-test"
    assert len(captured["message"]) == 256
    assert captured["context"]["api_key"] == "[REDACTED]"
    assert captured["context"]["authorization"] == "[REDACTED]"
    assert captured["context"]["nested"]["password"] == "[REDACTED]"
    assert captured["context"]["nested"]["safe_note"] == "ok"
    assert str(captured["context"]["long_text"]).endswith("[TRUNCATED]")


def test_control_tower_decision_details_mask_sensitive_values(monkeypatch) -> None:
    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(main_module, "record_control_tower_decision", _capture)

    main_module._safe_record_control_tower_decision(
        decision_id="ct-1",
        scenario_id="sc-1",
        user_id="u1",
        role="Ops",
        risk_score=0.5,
        risk_level="medium",
        spec_version="1.0.0",
        refusal=False,
        details={
            "token": "t-123",
            "actions": [
                {"name": "notify", "secret": "raw-secret"},
                {"name": "isolate"},
            ],
        },
    )

    assert captured["decision_id"] == "ct-1"
    assert captured["details"]["token"] == "[REDACTED]"
    assert captured["details"]["actions"][0]["secret"] == "[REDACTED]"
