from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.auth import create_jwt
import app.main as main_module


def _headers(role: str, user_id: str) -> dict:
    token = create_jwt(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_ops_runtime_requires_ops_or_admin() -> None:
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime",
            headers=_headers(role="Employee", user_id="employee-ops-runtime"),
        )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_ops_runtime_filters_events_and_sanitizes_decisions(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "summarize_log",
        lambda *_args, **_kwargs: {
            "requests": 12,
            "top_users": [("ops-user", 12)],
            "tools_used": [("runbook_lookup", 6)],
            "policy_events": [("refusal", 2)],
            "total_cost": 2.2,
        },
    )
    monkeypatch.setattr(main_module, "get_daily_cost", lambda: 4.5)
    monkeypatch.setattr(
        main_module,
        "evaluate_ops_alerts",
        lambda *_args, **_kwargs: [
            {
                "code": "high_refusal_ratio",
                "severity": "warning",
                "message": "Refusal ratio exceeded threshold.",
                "value": 0.3,
                "threshold": 0.2,
            }
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_service_events",
        lambda limit=25: [
            {
                "id": 2,
                "created_at": "2026-02-12T00:01:00+00:00",
                "level": "WARN",
                "component": "alerts",
                "message": "delivery failed",
                "context": {"failed": 1},
            },
            {
                "id": 1,
                "created_at": "2026-02-12T00:00:00+00:00",
                "level": "INFO",
                "component": "startup",
                "message": "startup ok",
                "context": {},
            },
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_control_tower_decisions",
        lambda limit=15: [
            {
                "decision_id": "ct-100",
                "created_at": "2026-02-12T00:00:00+00:00",
                "scenario_id": "scenario-100",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_score": 0.9,
                "risk_level": "critical",
                "spec_version": "1.0.0",
                "refusal": False,
                "details": {"internal": "not-returned"},
            }
        ],
    )
    main_module.app.state.startup_report = {
        "overall_status": "healthy",
        "startup_ready": True,
        "checks": [],
    }

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime?component=alerts&level=warn",
            headers=_headers(role="Ops", user_id="ops-runtime-filter"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["startup_status"] == "healthy"
    assert len(body["service_events"]) == 1
    assert body["service_events"][0]["component"] == "alerts"
    assert body["service_events"][0]["level"] == "WARN"
    assert len(body["recent_decisions"]) == 1
    assert "details" not in body["recent_decisions"][0]
    assert body["alerts"][0]["code"] == "high_refusal_ratio"


@pytest.mark.anyio
async def test_ops_diagnostics_refresh_updates_startup_report(monkeypatch) -> None:
    report = {
        "ok": False,
        "startup_ready": True,
        "overall_status": "degraded",
        "failed_checks": ["runbooks"],
        "failed_critical_checks": [],
        "failed_warning_checks": ["runbooks"],
        "checks": [],
    }

    monkeypatch.setattr(main_module, "run_startup_diagnostics", lambda **_kwargs: report)
    captured = {}

    def _capture_event(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(main_module, "_safe_record_service_event", _capture_event)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/ops/diagnostics/refresh",
            headers=_headers(role="Admin", user_id="admin-refresh"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["startup_status"] == "degraded"
    assert body["startup_report"] == report
    assert main_module.app.state.startup_report == report
    assert captured["component"] == "diagnostics"
    assert captured["level"] == "WARN"


@pytest.mark.anyio
async def test_ops_runtime_time_window_filters_events_and_decisions(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    recent_ts = now.isoformat()
    stale_ts = (now - timedelta(minutes=180)).isoformat()

    monkeypatch.setattr(
        main_module,
        "summarize_log",
        lambda *_args, **_kwargs: {
            "requests": 2,
            "top_users": [("ops-user", 2)],
            "tools_used": [],
            "policy_events": [],
            "total_cost": 0.0,
        },
    )
    monkeypatch.setattr(main_module, "get_daily_cost", lambda: 0.0)
    monkeypatch.setattr(main_module, "evaluate_ops_alerts", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        main_module,
        "get_recent_service_events",
        lambda limit=25: [
            {
                "id": 2,
                "created_at": recent_ts,
                "level": "INFO",
                "component": "diagnostics",
                "message": "recent",
                "context": {},
            },
            {
                "id": 1,
                "created_at": stale_ts,
                "level": "INFO",
                "component": "diagnostics",
                "message": "stale",
                "context": {},
            },
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_control_tower_decisions",
        lambda limit=15: [
            {
                "decision_id": "ct-recent",
                "created_at": recent_ts,
                "scenario_id": "scenario-recent",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_score": 0.4,
                "risk_level": "medium",
                "spec_version": "1.0.0",
                "refusal": False,
                "details": {},
            },
            {
                "decision_id": "ct-stale",
                "created_at": stale_ts,
                "scenario_id": "scenario-stale",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_score": 0.6,
                "risk_level": "high",
                "spec_version": "1.0.0",
                "refusal": False,
                "details": {},
            },
        ],
    )
    main_module.app.state.startup_report = {
        "overall_status": "healthy",
        "startup_ready": True,
        "checks": [],
    }

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime?events_since_minutes=60&decisions_since_minutes=60",
            headers=_headers(role="Ops", user_id="ops-window-filter"),
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["service_events"]) == 1
    assert body["service_events"][0]["message"] == "recent"
    assert len(body["recent_decisions"]) == 1
    assert body["recent_decisions"][0]["decision_id"] == "ct-recent"


@pytest.mark.anyio
async def test_ops_runtime_supports_search_level_alias_and_sort(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "summarize_log",
        lambda *_args, **_kwargs: {
            "requests": 3,
            "top_users": [("ops-user", 3)],
            "tools_used": [],
            "policy_events": [],
            "total_cost": 0.0,
        },
    )
    monkeypatch.setattr(main_module, "get_daily_cost", lambda: 0.0)
    monkeypatch.setattr(
        main_module,
        "evaluate_ops_alerts",
        lambda *_args, **_kwargs: [
            {
                "code": "high_refusal_ratio",
                "severity": "warning",
                "message": "Refusal ratio exceeded threshold.",
                "value": 0.3,
                "threshold": 0.2,
            },
            {
                "code": "daily_cost_threshold_exceeded",
                "severity": "critical",
                "message": "Daily LLM cost exceeded threshold.",
                "value": 70.0,
                "threshold": 50.0,
            },
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_service_events",
        lambda limit=25: [
            {
                "id": 3,
                "created_at": "2026-02-12T00:03:00+00:00",
                "level": "WARN",
                "component": "alerts-webhook",
                "message": "delivery failed",
                "context": {"failed": 1},
            },
            {
                "id": 2,
                "created_at": "2026-02-12T00:02:00+00:00",
                "level": "ERROR",
                "component": "diagnostics",
                "message": "validation failed",
                "context": {},
            },
            {
                "id": 1,
                "created_at": "2026-02-12T00:01:00+00:00",
                "level": "INFO",
                "component": "startup",
                "message": "startup ok",
                "context": {},
            },
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_control_tower_decisions",
        lambda limit=15: [
            {
                "decision_id": "ct-b",
                "created_at": "2026-02-12T00:03:00+00:00",
                "scenario_id": "scenario-beta",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_score": 0.8,
                "risk_level": "high",
                "spec_version": "1.0.0",
                "refusal": False,
                "details": {},
            },
            {
                "decision_id": "ct-a",
                "created_at": "2026-02-12T00:01:00+00:00",
                "scenario_id": "scenario-alpha",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_score": 0.4,
                "risk_level": "medium",
                "spec_version": "1.0.0",
                "refusal": False,
                "details": {},
            },
        ],
    )
    main_module.app.state.startup_report = {
        "overall_status": "healthy",
        "startup_ready": True,
        "checks": [],
    }

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime?component=alert&level=warning&search=failed&sort=asc",
            headers=_headers(role="Ops", user_id="ops-search-sort"),
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["service_events"]) == 1
    assert body["service_events"][0]["component"] == "alerts-webhook"
    assert body["service_events"][0]["level"] == "WARN"
    assert len(body["recent_decisions"]) == 0
    assert len(body["alerts"]) == 0
