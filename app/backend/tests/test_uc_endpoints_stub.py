import httpx
import pytest

from app.llm_adapter import reset_llm_runtime_settings, update_llm_runtime_settings
from app.main import app


async def _login(client: httpx.AsyncClient, *, user_id: str, role: str) -> str:
    res = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert res.status_code == 200, res.text
    payload = res.json()
    assert "access_token" in payload
    return payload["access_token"]


@pytest.mark.anyio
async def test_uc1_and_uc2_endpoints_work_in_stub_mode() -> None:
    # Ensure we never hit a real provider even if the environment is configured globally.
    update_llm_runtime_settings(provider="stub")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ops_token = await _login(client, user_id="ops-demo", role="Ops")
        headers = {"Authorization": f"Bearer {ops_token}"}

        uc1 = await client.post(
            "/uc1/architecture",
            headers=headers,
            json={
                "query": "Summarize handover risks for payments prod and propose next actions.",
                "system": "payments",
                "env": "prod",
                "citation_only": False,
            },
        )
        assert uc1.status_code == 200, uc1.text
        uc1_payload = uc1.json()
        assert isinstance(uc1_payload.get("answer"), str) and uc1_payload["answer"].strip()
        assert isinstance(uc1_payload.get("citations"), list)
        assert len(uc1_payload["citations"]) >= 1

        uc2 = await client.post(
            "/uc2/log-intel",
            headers=headers,
            json={
                "logs": "2026-02-12T10:15:22Z ERROR Timeout while calling payments API",
                "system": "payments",
                "env": "prod",
            },
        )
        assert uc2.status_code == 200, uc2.text
        uc2_payload = uc2.json()
        assert isinstance(uc2_payload.get("summary"), str) and uc2_payload["summary"].strip()
        assert isinstance(uc2_payload.get("root_causes"), list) and len(uc2_payload["root_causes"]) >= 1
        assert isinstance(uc2_payload.get("runbook_steps"), list) and len(uc2_payload["runbook_steps"]) >= 1
    reset_llm_runtime_settings()
