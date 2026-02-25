import httpx
import pytest

import app.llm_adapter as llm_adapter
import app.main as main_module
from app.llm_adapter import OllamaAdapter, get_llm_adapter, reset_llm_runtime_settings, update_llm_runtime_settings


async def _login(client: httpx.AsyncClient, *, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    payload = response.json()
    return str(payload.get("access_token", ""))


@pytest.mark.anyio
async def test_admin_runtime_accepts_ollama_provider_and_normalizes_model() -> None:
    reset_llm_runtime_settings()

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _login(client, user_id="admin-ollama", role="Admin")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            "/admin/runtime/llm",
            headers=headers,
            json={
                "provider": "ollama",
                "model": "stub-llm",
                "ollama_base_url": "http://127.0.0.1:11434",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()

    assert payload["provider"] == "ollama"
    assert payload["model"] == "llama3.1:8b"
    assert payload["ollama_base_url"] == "http://127.0.0.1:11434"
    reset_llm_runtime_settings()


def test_get_llm_adapter_returns_ollama_adapter() -> None:
    update_llm_runtime_settings(provider="ollama", model="stub-llm")
    adapter = get_llm_adapter()
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "llama3.1:8b"
    reset_llm_runtime_settings()


def test_ollama_adapter_calls_api_chat(monkeypatch) -> None:
    update_llm_runtime_settings(
        provider="ollama",
        model="llama3.1:8b",
        temperature=0.3,
        max_tokens=256,
        timeout_sec=15,
        ollama_base_url="http://127.0.0.1:11434",
    )

    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "message": {"role": "assistant", "content": "Local Ollama response"},
                "prompt_eval_count": 9,
                "eval_count": 4,
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(llm_adapter.requests, "post", fake_post)
    adapter = get_llm_adapter()
    result = adapter.generate(
        messages=[
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Analyze operational risk signals."},
        ],
        use_case="uc1",
    )

    assert result.text == "Local Ollama response"
    assert result.tokens_in == 9
    assert result.tokens_out == 4
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["json"]["model"] == "llama3.1:8b"
    assert captured["json"]["stream"] is False
    assert captured["json"]["options"]["num_predict"] == 256
    assert captured["json"]["options"]["temperature"] == 0.3
    reset_llm_runtime_settings()
