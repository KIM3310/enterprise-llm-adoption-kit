from types import SimpleNamespace

import jwt

import app.alerts as alerts
import app.auth as auth
import app.storage as storage


def test_jwt_rotation_uses_active_kid(monkeypatch) -> None:
    monkeypatch.setattr(
        auth,
        "settings",
        SimpleNamespace(
            jwt_secret="fallback-secret",
            jwt_secrets={
                "v1": "rotation-secret-v1-32-byte-minimum",
                "v2": "rotation-secret-v2-32-byte-minimum",
            },
            jwt_active_kid="v2",
            jwt_issuer="test-issuer",
            jwt_ttl_minutes=60,
            auth_mode="local_jwt",
            oidc_issuer="",
            oidc_audience="",
            oidc_jwks_url="",
            oidc_algorithms=["RS256"],
        ),
    )

    token = auth.create_jwt("user-rotation", "Admin")
    header = jwt.get_unverified_header(token)
    assert header["kid"] == "v2"

    user = auth.decode_jwt(token)
    assert user.user_id == "user-rotation"
    assert user.roles == ["Admin"]


def test_auth_key_metadata_exposes_kids(monkeypatch) -> None:
    monkeypatch.setattr(
        auth,
        "settings",
        SimpleNamespace(
            jwt_secret="fallback-secret",
            jwt_secrets={
                "v1": "rotation-secret-v1-32-byte-minimum",
                "v2": "rotation-secret-v2-32-byte-minimum",
            },
            jwt_active_kid="v2",
            auth_mode="local_jwt",
        ),
    )
    metadata = auth.auth_key_metadata()
    assert metadata["active_kid"] == "v2"
    assert metadata["kids"] == ["v1", "v2"]


def test_evaluate_ops_alerts_detects_ratio_and_cost(monkeypatch) -> None:
    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_min_requests=10,
            ops_alert_refusal_ratio_threshold=0.2,
            ops_alert_injection_ratio_threshold=0.1,
            ops_alert_daily_cost_threshold_usd=10.0,
            ops_alert_webhook_url="",
            ops_alert_webhook_timeout_sec=5.0,
        ),
    )

    summary = {
        "requests": 20,
        "policy_events": [("refusal", 6), ("injection_detected", 3)],
    }
    found = alerts.evaluate_ops_alerts(summary, daily_cost_usd=12.3)
    codes = {item["code"] for item in found}

    assert "high_refusal_ratio" in codes
    assert "high_injection_ratio" in codes
    assert "daily_cost_threshold_exceeded" in codes


def test_jsonl_storage_backend_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        storage,
        "settings",
        SimpleNamespace(
            sqlite_path=str(tmp_path / "app.db"),
            event_storage_backend="jsonl",
            service_events_jsonl_path=str(tmp_path / "service_events.jsonl"),
            control_tower_decisions_jsonl_path=str(tmp_path / "ct.jsonl"),
            daily_cost_json_path=str(tmp_path / "daily_costs.json"),
        ),
    )

    storage.init_db()
    storage.record_service_event("INFO", "ops", "jsonl event", {"from": "test"})
    storage.record_control_tower_decision(
        decision_id="ct-jsonl-1",
        scenario_id="scenario-jsonl",
        user_id="ops-user",
        role="Ops",
        risk_score=0.8,
        risk_level="high",
        spec_version="1.0.0",
        refusal=False,
        details={"source": "jsonl"},
    )
    storage.add_cost(1.25)

    events = storage.get_recent_service_events(limit=5)
    decisions = storage.get_recent_control_tower_decisions(limit=5)
    total = storage.get_daily_cost()

    assert events[0]["component"] == "ops"
    assert decisions[0]["decision_id"] == "ct-jsonl-1"
    assert round(total, 2) == 1.25
