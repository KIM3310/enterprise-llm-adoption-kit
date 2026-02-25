import httpx
import pytest

import app.main as main_module

EXPECTED_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}


class _SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


def _assert_standard_headers(response: httpx.Response) -> None:
    assert response.headers.get("cache-control") == "no-store"
    request_id = response.headers.get("x-request-id", "")
    assert request_id.startswith("req-")
    for header_name, expected in EXPECTED_SECURITY_HEADERS.items():
        assert response.headers.get(header_name) == expected


@pytest.mark.anyio
async def test_success_responses_include_standard_security_headers() -> None:
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    _assert_standard_headers(response)


@pytest.mark.anyio
async def test_http_exceptions_include_standard_security_headers(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, integrations_require_auth=True),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/integrations/slack/events",
            json={"user_id": "u1", "text": "hello", "role": "Employee"},
        )

    assert response.status_code == 401
    body = response.json()
    assert body["request_id"] == response.headers.get("x-request-id")
    _assert_standard_headers(response)


@pytest.mark.anyio
async def test_request_body_size_limit_returns_413(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, request_max_body_bytes=64),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={
                "user_id": "demo-user",
                "role": "Employee",
                "login_code": "x" * 400,
            },
        )

    assert response.status_code == 413
    body = response.json()
    assert "Request body too large" in str(body.get("detail", ""))
    assert body["request_id"] == response.headers.get("x-request-id")
    _assert_standard_headers(response)
