import httpx
import pytest


async def _token(client: httpx.AsyncClient, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_login_rejects_user_id_with_whitespace() -> None:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={"user_id": "bad user", "role": "Employee"},
        )

    assert response.status_code == 422
    assert "user_id" in response.text


@pytest.mark.anyio
async def test_uc1_rejects_blank_query() -> None:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "uc1-user", "Employee")
        response = await client.post(
            "/uc1/architecture",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "   "},
        )

    assert response.status_code == 422
    assert "query" in response.text


@pytest.mark.anyio
async def test_uc2_rejects_blank_logs() -> None:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "uc2-user", "Ops")
        response = await client.post(
            "/uc2/log-intel",
            headers={"Authorization": f"Bearer {token}"},
            json={"logs": "   \n\t"},
        )

    assert response.status_code == 422
    assert "logs" in response.text


@pytest.mark.anyio
async def test_jira_rejects_overlong_description() -> None:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "jira-user", "Ops")
        response = await client.post(
            "/integrations/jira/ticket",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ticket_id": "INC-1000",
                "title": "timeout",
                "description": "x" * 13000,
                "priority": "High",
                "reporter": "jira-user",
                "role": "Ops",
            },
        )

    assert response.status_code == 422
    assert "description" in response.text
