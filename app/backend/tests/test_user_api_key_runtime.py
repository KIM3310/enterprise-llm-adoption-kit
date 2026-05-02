import httpx
import pytest

import app.llm_adapter as llm_adapter
import app.main as main_module
from app.llm_adapter import clear_user_openai_api_key, reset_llm_runtime_settings, update_llm_runtime_settings


async def _login(client: httpx.AsyncClient, *, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    payload = response.json()
    return str(payload.get("access_token", ""))


@pytest.mark.anyio
async def test_user_api_key_crud_exposes_effective_runtime() -> None:
    update_llm_runtime_settings(provider="stub", model="stub-llm", openai_api_key="")
    user_id = "byok-user"
    clear_user_openai_api_key(user_id)

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _login(client, user_id=user_id, role="Employee")
        headers = {"Authorization": f"Bearer {token}"}

        status_before = await client.get("/runtime/user-api-key", headers=headers)
        assert status_before.status_code == 200, status_before.text
        before_payload = status_before.json()
        assert before_payload["openai_api_key_configured"] is False
        assert before_payload["effective_provider"] == "stub"

        save_response = await client.post(
            "/runtime/user-api-key",
            headers=headers,
            json={"openai_api_key": "test-byok-user-key-12345678901234567890"},
        )
        assert save_response.status_code == 200, save_response.text
        save_payload = save_response.json()
        assert save_payload["openai_api_key_configured"] is True
        assert save_payload["effective_provider"] == "openai"
        assert save_payload["effective_model"] == "gpt-4o-mini"

        remove_response = await client.delete("/runtime/user-api-key", headers=headers)
        assert remove_response.status_code == 200, remove_response.text
        remove_payload = remove_response.json()
        assert remove_payload["openai_api_key_configured"] is False
        assert remove_payload["effective_provider"] == "stub"

    clear_user_openai_api_key(user_id)
    reset_llm_runtime_settings()


@pytest.mark.anyio
async def test_uc1_uses_user_api_key_override_when_runtime_provider_is_stub(monkeypatch) -> None:
    update_llm_runtime_settings(provider="stub", model="stub-llm", openai_api_key="")
    user_id = "byok-uc1-user"
    clear_user_openai_api_key(user_id)

    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": "BYOK response"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4},
            }

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(llm_adapter.requests, "post", fake_post)
    monkeypatch.setattr(main_module.rag_store, "ensure_index", lambda: None)
    monkeypatch.setattr(main_module.rag_store, "query", lambda *_args, **_kwargs: [])

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _login(client, user_id=user_id, role="Ops")
        headers = {"Authorization": f"Bearer {token}"}

        save_response = await client.post(
            "/runtime/user-api-key",
            headers=headers,
            json={"openai_api_key": "test-uc1-user-key-12345678901234567890"},
        )
        assert save_response.status_code == 200, save_response.text

        uc1_response = await client.post(
            "/uc1/architecture",
            headers=headers,
            json={
                "query": "Summarize architecture risks for the payments service.",
                "citation_only": False,
            },
        )
        assert uc1_response.status_code == 200, uc1_response.text
        assert "BYOK response" in str(uc1_response.json().get("answer", ""))

    assert captured.get("headers", {}).get("Authorization") == "Bearer test-uc1-user-key-12345678901234567890"
    assert str(captured.get("url", "")).endswith("/chat/completions")
    assert captured.get("json", {}).get("model") == "gpt-4o-mini"

    clear_user_openai_api_key(user_id)
    reset_llm_runtime_settings()
