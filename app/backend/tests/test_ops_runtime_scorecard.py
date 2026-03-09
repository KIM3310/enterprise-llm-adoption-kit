import httpx
import pytest

from app.auth import create_jwt
import app.main as main_module


def _headers(role: str, user_id: str) -> dict:
    token = create_jwt(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_ops_runtime_scorecard_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "summarize_log",
        lambda *_args, **_kwargs: {
            "requests": 9,
            "top_users": [("ops-user", 9)],
            "tools_used": [("runbook_lookup", 4)],
            "policy_events": [("refusal", 1)],
            "total_cost": 1.2,
        },
    )
    monkeypatch.setattr(main_module, "get_daily_cost", lambda: 3.25)
    monkeypatch.setattr(
        main_module,
        "evaluate_ops_alerts",
        lambda *_args, **_kwargs: [
            {
                "code": "high_refusal_ratio",
                "severity": "warning",
                "message": "Refusal ratio exceeded threshold.",
            }
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_service_events",
        lambda limit=10: [
            {
                "created_at": "2026-03-09T00:00:00+00:00",
                "level": "WARN",
                "component": "alerts",
                "message": "delivery failed",
            }
        ],
    )
    monkeypatch.setattr(
        main_module,
        "get_recent_control_tower_decisions",
        lambda limit=10: [
            {
                "decision_id": "ct-200",
                "created_at": "2026-03-09T00:00:00+00:00",
                "scenario_id": "scenario-200",
                "user_id": "ops-user",
                "role": "Ops",
                "risk_level": "high",
            }
        ],
    )
    main_module.app.state.startup_report = {
        "overall_status": "healthy",
        "startup_ready": True,
        "failed_checks": [],
    }

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime/scorecard",
            headers=_headers(role="Ops", user_id="ops-scorecard"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "enterprise-ops-runtime-scorecard-v1"
    assert body["summary"]["request_count"] == 9
    assert body["summary"]["alert_count"] == 1
    assert body["runtime"]["storage_backend"] in {"sqlite", "jsonl"}
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"
    assert body["top_alert"]["code"] == "high_refusal_ratio"


@pytest.mark.anyio
async def test_ops_runtime_scorecard_requires_ops_or_admin() -> None:
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime/scorecard",
            headers=_headers(role="Employee", user_id="employee-scorecard"),
        )

    assert response.status_code == 403
