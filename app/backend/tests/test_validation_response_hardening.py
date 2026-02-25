import httpx
import pytest

import app.main as main_module


@pytest.mark.anyio
async def test_validation_errors_use_standard_shape_with_request_id() -> None:
    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/auth/login",
            json={"user_id": "bad user", "role": "Employee"},
        )

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body.get("detail"), dict)
    assert body["detail"].get("message") == "Request validation failed"
    assert isinstance(body["detail"].get("errors"), list)
    assert body["request_id"] == response.headers.get("x-request-id")
