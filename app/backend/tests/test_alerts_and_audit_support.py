import hashlib
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import requests

import app.alerts as alerts
import app.config as config


def _load_audit_module(monkeypatch, tmp_path, *, mode: str, retention_days: int):
    existing = sys.modules.get("app.audit")
    if existing is not None and hasattr(existing, "logger"):
        for handler in existing.logger.handlers[:]:
            existing.logger.removeHandler(handler)
            handler.close()

    settings = SimpleNamespace(
        audit_log_path=str(tmp_path / "audit.log"),
        audit_retention_days=retention_days,
        data_handling_mode=mode,
    )
    monkeypatch.setattr(config, "settings", settings, raising=False)
    audit = importlib.import_module("app.audit")
    return importlib.reload(audit)


def test_policy_counts_and_threshold_alerts(monkeypatch) -> None:
    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_min_requests=20,
            ops_alert_refusal_ratio_threshold=0.2,
            ops_alert_injection_ratio_threshold=0.1,
            ops_alert_daily_cost_threshold_usd=50.0,
        ),
    )
    summary = {
        "requests": 100,
        "policy_events": [
            ("refusal", 25),
            ("injection_detected", 15),
            ("ignored", 1),
            ("bad-item",),
            (1, 2),
        ],
    }

    triggered = alerts.evaluate_ops_alerts(summary, daily_cost_usd=75.5)

    assert [item["code"] for item in triggered] == [
        "high_refusal_ratio",
        "high_injection_ratio",
        "daily_cost_threshold_exceeded",
    ]
    assert triggered[0]["value"] == 0.25
    assert triggered[1]["value"] == 0.15
    assert triggered[2]["severity"] == "critical"


def test_alert_evaluation_respects_min_request_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_min_requests=20,
            ops_alert_refusal_ratio_threshold=0.01,
            ops_alert_injection_ratio_threshold=0.01,
            ops_alert_daily_cost_threshold_usd=999.0,
        ),
    )

    triggered = alerts.evaluate_ops_alerts(
        {
            "requests": 5,
            "policy_events": [("refusal", 5), ("injection_detected", 5)],
        },
        daily_cost_usd=10.0,
    )

    assert triggered == []


def test_dispatch_ops_alerts_success(monkeypatch) -> None:
    captured = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

    def _fake_post(url, *, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_webhook_url="https://hooks.example.test/ops",
            ops_alert_webhook_timeout_sec=2.5,
        ),
    )
    monkeypatch.setattr(alerts.requests, "post", _fake_post)

    result = alerts.dispatch_ops_alerts(
        [{"code": "high_refusal_ratio"}],
        {"requests": 42},
        12.345678,
    )

    assert result == {"sent": 1, "failed": 0}
    assert captured["url"] == "https://hooks.example.test/ops"
    assert captured["timeout"] == 2.5
    assert captured["json"]["requests"] == 42
    assert captured["json"]["daily_cost_usd"] == 12.345678


def test_dispatch_ops_alerts_failure_and_short_circuit(monkeypatch) -> None:
    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_webhook_url="",
            ops_alert_webhook_timeout_sec=0.1,
        ),
    )
    assert alerts.dispatch_ops_alerts([], {"requests": 1}, 1.0) == {
        "sent": 0,
        "failed": 0,
    }

    def _failing_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(
        alerts,
        "settings",
        SimpleNamespace(
            ops_alert_webhook_url="https://hooks.example.test/ops",
            ops_alert_webhook_timeout_sec=0.2,
        ),
    )
    monkeypatch.setattr(alerts.requests, "post", _failing_post)

    assert alerts.dispatch_ops_alerts(
        [{"code": "daily_cost_threshold_exceeded"}],
        {"requests": 3},
        51.0,
    ) == {"sent": 0, "failed": 1}


def test_build_payload_hashes_enterprise_mode(monkeypatch, tmp_path) -> None:
    audit = _load_audit_module(
        monkeypatch, tmp_path, mode="enterprise", retention_days=7
    )

    payload = audit.build_payload("hello", "world")

    assert payload == {
        "input_hash": hashlib.sha256(b"hello").hexdigest(),
        "output_hash": hashlib.sha256(b"world").hexdigest(),
        "mode": "enterprise",
    }


def test_build_payload_keeps_raw_content_in_demo_mode(monkeypatch, tmp_path) -> None:
    audit = _load_audit_module(monkeypatch, tmp_path, mode="demo", retention_days=7)

    payload = audit.build_payload("hello", "world")

    assert payload == {
        "input": "hello",
        "output": "world",
        "mode": "demo",
    }


def test_prune_if_needed_filters_old_invalid_and_missing_timestamps(
    monkeypatch, tmp_path
) -> None:
    audit = _load_audit_module(
        monkeypatch, tmp_path, mode="enterprise", retention_days=7
    )
    audit_path = Path(audit.settings.audit_log_path)
    now = datetime.now(timezone.utc)
    audit_path.write_text(
        "\n".join(
            [
                json.dumps({"timestamp": now.isoformat(), "event": "keep"}),
                json.dumps(
                    {
                        "timestamp": (
                            now - timedelta(days=30)
                        ).isoformat(),
                        "event": "drop",
                    }
                ),
                json.dumps({"event": "missing-ts"}),
                "{not-json}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    audit._prune_if_needed()

    remaining = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(remaining) == 1
    assert json.loads(remaining[0])["event"] == "keep"


def test_prune_if_needed_returns_early_for_demo_disabled_and_missing_files(
    monkeypatch, tmp_path
) -> None:
    demo_audit = _load_audit_module(
        monkeypatch, tmp_path, mode="demo", retention_days=7
    )
    demo_path = Path(demo_audit.settings.audit_log_path)
    demo_audit._prune_if_needed()
    assert demo_path.exists()
    assert demo_path.read_text(encoding="utf-8") == ""

    missing_audit = _load_audit_module(
        monkeypatch, tmp_path, mode="enterprise", retention_days=7
    )
    missing_path = Path(missing_audit.settings.audit_log_path)
    missing_path.unlink()
    missing_audit._prune_if_needed()
    assert not missing_path.exists()

    disabled_audit = _load_audit_module(
        monkeypatch, tmp_path, mode="enterprise", retention_days=0
    )
    disabled_path = Path(disabled_audit.settings.audit_log_path)
    disabled_path.write_text("keep-me\n", encoding="utf-8")
    disabled_audit._prune_if_needed()
    assert disabled_path.read_text(encoding="utf-8") == "keep-me\n"


def test_log_audit_prunes_then_writes_timestamped_event(monkeypatch, tmp_path) -> None:
    audit = _load_audit_module(
        monkeypatch, tmp_path, mode="enterprise", retention_days=7
    )
    calls = {"count": 0}
    original_prune = audit._prune_if_needed

    def _spy_prune() -> None:
        calls["count"] += 1
        original_prune()

    monkeypatch.setattr(audit, "_prune_if_needed", _spy_prune)

    audit.log_audit({"event": "handoff", "actor": "ops"})
    for handler in audit.logger.handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    lines = Path(audit.settings.audit_log_path).read_text(encoding="utf-8").strip().splitlines()
    body = json.loads(lines[-1])

    assert calls["count"] == 1
    assert body["event"] == "handoff"
    assert body["actor"] == "ops"
    assert body["timestamp"].endswith("+00:00")
