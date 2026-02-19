import httpx
import pytest

import app.main as main_module
from app.auth import create_jwt_for_roles
from app.models import HandoverResponse, LogIntelResponse


class _SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


async def _token(client: httpx.AsyncClient, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_integrations_require_auth_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=True),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        slack = await client.post(
            "/integrations/slack/events",
            json={"user_id": "u1", "text": "hello", "channel": "c1", "role": "Employee"},
        )
        jira = await client.post(
            "/integrations/jira/ticket",
            json={
                "ticket_id": "INC-1",
                "title": "timeout",
                "description": "ERROR Timeout while calling payments API",
                "priority": "High",
                "reporter": "u2",
                "role": "Ops",
            },
        )

    assert slack.status_code == 401
    assert jira.status_code == 401


@pytest.mark.anyio
async def test_slack_uses_bearer_role_over_payload_role(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=True),
    )
    captured = {}

    def _fake_handover(payload, user):
        captured["user_id"] = user.user_id
        captured["roles"] = list(user.roles)
        return HandoverResponse(answer="ok", citations=[])

    monkeypatch.setattr(main_module, "handover", _fake_handover)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "secure-admin", "Admin")
        response = await client.post(
            "/integrations/slack/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "payload-user",
                "text": "/uc1 summarize risks",
                "channel": "sec-c1",
                "role": "Employee",
            },
        )

    assert response.status_code == 200, response.text
    assert captured["roles"] == ["Admin"]
    assert captured["user_id"] == "slack-secure-admin"


@pytest.mark.anyio
async def test_jira_uses_bearer_role_over_payload_role(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=True),
    )
    captured = {}

    def _fake_log_intel(payload, user):
        captured["user_id"] = user.user_id
        captured["roles"] = list(user.roles)
        return LogIntelResponse(
            summary="summary",
            root_causes=["root cause"],
            runbook_steps=["step-1"],
            tool_calls=[],
        )

    monkeypatch.setattr(main_module, "log_intel", _fake_log_intel)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _token(client, "ops-user", "Ops")
        response = await client.post(
            "/integrations/jira/ticket",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ticket_id": "INC-123",
                "title": "timeout",
                "description": "ERROR Timeout while calling payments API",
                "priority": "High",
                "reporter": "payload-reporter",
                "role": "Admin",
            },
        )

    assert response.status_code == 200, response.text
    assert captured["roles"] == ["Ops"]
    assert captured["user_id"] == "jira-ops-user"


@pytest.mark.anyio
async def test_slack_prefers_highest_privilege_role_for_multi_role_token(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=True),
    )
    captured = {}

    def _fake_handover(payload, user):
        captured["user_id"] = user.user_id
        captured["roles"] = list(user.roles)
        return HandoverResponse(answer="ok", citations=[])

    monkeypatch.setattr(main_module, "handover", _fake_handover)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = create_jwt_for_roles("multi-role-user", ["Employee", "Admin"])
        response = await client.post(
            "/integrations/slack/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "payload-user",
                "text": "/uc1 summarize risks",
                "channel": "sec-c1",
                "role": "Employee",
            },
        )

    assert response.status_code == 200, response.text
    assert captured["roles"] == ["Admin"]
    assert captured["user_id"] == "slack-multi-role-user"


@pytest.mark.anyio
async def test_slack_allows_unauth_when_policy_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=False),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/integrations/slack/events",
            json={"user_id": "u1", "text": "hello", "channel": "c1", "role": "Employee"},
        )

    assert response.status_code == 200, response.text
    assert "Usage" in response.json()["text"]
