import httpx
import pytest

import app.main as main_module


class _SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


@pytest.mark.anyio
async def test_login_requires_code_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, demo_login_code="atelier-2026"),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={"user_id": "demo-user", "role": "Employee"},
        )

    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid login code"


@pytest.mark.anyio
async def test_login_accepts_code_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, demo_login_code="atelier-2026"),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={"user_id": "demo-user", "role": "Employee", "login_code": "atelier-2026"},
        )

    assert response.status_code == 200, response.text
    assert isinstance(response.json().get("access_token"), str)
