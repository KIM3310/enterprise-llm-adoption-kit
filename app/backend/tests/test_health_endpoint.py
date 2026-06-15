import httpx
import pytest

from app.llm_adapter import reset_llm_runtime_settings, update_llm_runtime_settings
from app.main import app


@pytest.mark.anyio
async def test_health_includes_runtime_metadata() -> None:
    update_llm_runtime_settings(provider="stub", model="stub-llm", openai_api_key="")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200, res.text
        payload = res.json()

    assert payload.get("status") in {"ok", "degraded"}
    assert isinstance(payload.get("startup_status", ""), str)
    assert str(payload.get("service", "")).startswith("Enterprise LLM Adoption Kit")

    assert payload.get("llm_provider") == "stub"
    assert payload.get("llm_model") == "stub-llm"
    assert payload.get("openai_api_key_configured") is False

    # These keys should be present for UI preflight / demos.
    assert payload.get("auth_mode") in {"local_jwt", "oidc"}
    assert payload.get("data_handling_mode") in {"demo", "enterprise"}
    assert payload.get("storage_backend") in {"sqlite", "jsonl"}
    assert payload.get("integrations_require_auth") in {True, False}
    assert payload.get("llm_fallback_to_stub_on_error") in {True, False}
    assert payload.get("llm_circuit_state") in {"open", "closed"}
    assert isinstance(payload.get("llm_circuit_open_seconds_remaining"), int)
    assert isinstance(payload.get("llm_circuit_consecutive_failures"), int)
    assert isinstance(payload.get("request_max_body_bytes"), int)
    assert payload.get("request_max_body_bytes", 0) >= 1024
    assert payload.get("links", {}).get("ops_runtime_scorecard") == "/ops/runtime/scorecard"
    assert payload.get("links", {}).get("ops_runtime") == "/ops/runtime"
    assert payload.get("links", {}).get("resource_pack") == "/ops/resource-pack"
    assert payload.get("architecture_fast_path") == [
        "/health",
        "/ops/service-brief",
        "/ops/resource-pack",
        "/ops/summary-pack",
        "/ops/rollout-gates",
        "/ops/review-summary",
        "/ops/runtime/scorecard",
    ]
    assert "ops-runtime-observability" in payload.get("capabilities", [])
    assert "diagnostics" in payload
    assert "next_action" in payload["diagnostics"]
    assert payload.get("ops_contract", {}).get("schema") == "ops-envelope-v1"

    reset_llm_runtime_settings()
