import httpx
import pytest

from app.main import app


async def _token(client: httpx.AsyncClient, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_jira_ticket_integration() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "sre.user", "Ops")
        response = await client.post(
            "/integrations/jira/ticket",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ticket_id": "PAY-1",
                "title": "Timeouts in payments",
                "description": "ERROR Timeout while calling payments API",
                "priority": "P1",
                "reporter": "sre.user",
                "role": "Employee",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ticket_id"] == "PAY-1"
    assert "Summary" in body["comment"]
