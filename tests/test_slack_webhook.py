import httpx
import pytest

from app.main import app


async def _token(client: httpx.AsyncClient, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_slack_uc1_route() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "U1", "Ops")
        response = await client.post(
            "/integrations/slack/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "U1",
                "text": "/uc1 Summarize handover risks for payments",
                "channel": "C1",
                "role": "Employee",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "Architecture Summary" in body["text"]


@pytest.mark.anyio
async def test_slack_unknown_command() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "U2", "Employee")
        response = await client.post(
            "/integrations/slack/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "U2",
                "text": "hello",
                "channel": "C2",
                "role": "Ops",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "Usage" in body["text"]
