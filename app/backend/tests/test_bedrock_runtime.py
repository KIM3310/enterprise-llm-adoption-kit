import sys
import types

import httpx
import pytest

import app.llm_adapter as llm_adapter
import app.main as main_module
from app.llm_adapter import BedrockAdapter, get_llm_adapter, reset_llm_runtime_settings, update_llm_runtime_settings


async def _login(client: httpx.AsyncClient, *, user_id: str, role: str) -> str:
    response = await client.post("/auth/login", json={"user_id": user_id, "role": role})
    assert response.status_code == 200, response.text
    payload = response.json()
    return str(payload.get("access_token", ""))


@pytest.mark.anyio
async def test_admin_runtime_accepts_bedrock_provider_and_normalizes_model() -> None:
    reset_llm_runtime_settings()

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        token = await _login(client, user_id="admin-bedrock", role="Admin")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            "/admin/runtime/llm",
            headers=headers,
            json={
                "provider": "bedrock",
                "model": "stub-llm",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()

    assert payload["provider"] == "bedrock"
    assert payload["model"] == "amazon.nova-micro-v1:0"
    reset_llm_runtime_settings()


def test_get_llm_adapter_returns_bedrock_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    update_llm_runtime_settings(provider="bedrock", model="stub-llm")
    adapter = get_llm_adapter()
    assert isinstance(adapter, BedrockAdapter)
    assert adapter.model == "amazon.nova-micro-v1:0"
    assert adapter.region == "us-east-1"
    reset_llm_runtime_settings()


def test_bedrock_adapter_calls_converse(monkeypatch: pytest.MonkeyPatch) -> None:
    update_llm_runtime_settings(
        provider="bedrock",
        model="amazon.nova-micro-v1:0",
        temperature=0.3,
        max_tokens=256,
        timeout_sec=15,
    )
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    captured: dict = {}

    class FakeClient:
        def converse(self, **kwargs):  # type: ignore[no-untyped-def]
            captured["kwargs"] = kwargs
            return {
                "output": {
                    "message": {
                        "content": [{"text": "Bedrock response"}],
                    }
                },
                "usage": {"inputTokens": 9, "outputTokens": 4},
            }

    fake_boto3 = types.SimpleNamespace(
        client=lambda service_name, region_name=None, config=None: (
            captured.update(
                {
                    "service_name": service_name,
                    "region_name": region_name,
                    "config": config,
                }
            )
            or FakeClient()
        )
    )

    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    adapter = get_llm_adapter()
    result = adapter.generate(
        messages=[
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Analyze adoption risk."},
        ],
        use_case="uc1",
    )

    assert result.text == "Bedrock response"
    assert result.tokens_in == 9
    assert result.tokens_out == 4
    assert captured["service_name"] == "bedrock-runtime"
    assert captured["region_name"] == "us-east-1"
    assert captured["kwargs"]["modelId"] == "amazon.nova-micro-v1:0"
    assert captured["kwargs"]["inferenceConfig"]["maxTokens"] == 256
    assert captured["kwargs"]["inferenceConfig"]["temperature"] == 0.3
    assert captured["kwargs"]["system"] == [{"text": "system"}]
    reset_llm_runtime_settings()
