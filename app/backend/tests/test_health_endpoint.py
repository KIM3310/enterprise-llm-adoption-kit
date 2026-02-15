from fastapi.testclient import TestClient

from app.llm_adapter import reset_llm_runtime_settings, update_llm_runtime_settings
from app.main import app


def test_health_includes_runtime_metadata() -> None:
    update_llm_runtime_settings(provider="stub", model="stub-llm", openai_api_key="")

    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200, res.text
        payload = res.json()

        assert payload.get("status") in {"ok", "degraded"}
        assert isinstance(payload.get("startup_status", ""), str)

        assert payload.get("llm_provider") == "stub"
        assert payload.get("llm_model") == "stub-llm"
        assert payload.get("openai_api_key_configured") is False

        # These keys should be present for UI preflight / demos.
        assert payload.get("auth_mode") in {"local_jwt", "oidc"}
        assert payload.get("data_handling_mode") in {"demo", "enterprise"}
        assert payload.get("storage_backend") in {"sqlite", "jsonl"}

    reset_llm_runtime_settings()

