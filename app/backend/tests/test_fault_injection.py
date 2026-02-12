import httpx
import pytest

from app.auth import create_jwt
from app.control_tower_service import ControlTowerService
import app.main as main_module


def _headers(role: str, user_id: str) -> dict:
    token = create_jwt(user_id=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


def _payload() -> dict:
    return {
        "scenario_id": "fault-injection-001",
        "region": "us-east-1",
        "notes": "fault injection test",
        "signals": {
            "demand_delta_ratio": 0.25,
            "inventory_days": 5.0,
            "machine_anomaly_score": 0.45,
            "sla_breach_risk": 0.52,
            "unit_margin_ratio": 0.14,
            "gpu_utilization": 0.73,
        },
        "targets": {
            "aws": True,
            "databricks": True,
            "snowflake": True,
            "palantir": True,
            "mariadb": True,
        },
    }


@pytest.mark.anyio
async def test_fault_injection_decision_builder_failure(monkeypatch) -> None:
    def _failing_builder(_):
        raise RuntimeError("injected build failure")

    monkeypatch.setattr(
        main_module,
        "control_tower_service",
        ControlTowerService(decision_builder=_failing_builder),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/control-tower/decision",
            json=_payload(),
            headers=_headers(role="Ops", user_id="ops-fi-1"),
        )

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Failed to build control tower decision"
    assert body["request_id"].startswith("req-")


@pytest.mark.anyio
async def test_fault_injection_decision_journal_write_failure_is_non_blocking(monkeypatch) -> None:
    def _failing_persist(*args, **kwargs):
        raise RuntimeError("injected sqlite write failure")

    monkeypatch.setattr(main_module, "record_control_tower_decision", _failing_persist)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/control-tower/decision",
            json=_payload(),
            headers=_headers(role="Admin", user_id="admin-fi-2"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"].startswith("ct-")
    assert body["risk_level"] in {"low", "medium", "high", "critical", "blocked"}


@pytest.mark.anyio
async def test_fault_injection_middleware_handles_unexpected_exception(monkeypatch) -> None:
    def _failing_summarize(_):
        raise RuntimeError("injected summary crash")

    monkeypatch.setattr(main_module, "summarize_log", _failing_summarize)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/audit/summary")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"].startswith("req-")
    assert response.headers["x-request-id"] == body["request_id"]
