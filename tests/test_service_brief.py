import httpx
import pytest

from app.main import app


@pytest.mark.anyio
async def test_ops_service_brief_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/service-brief")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-service-brief-v1"
    assert body["runtime"]["auth_mode"] == "local_jwt"
    assert body["runtime"]["llm_provider"] == "stub"
    assert body["evidence"]["test_files"] >= 20
    assert "aws" in body["platform_targets"]
    assert body["links"]["service_brief_schema"] == "/ops/service-brief/schema"
    assert any(stage["key"] == "operations" for stage in body["stages"])
    assert any(step["endpoint"] == "/auth/login" for step in body["review_flow"])


@pytest.mark.anyio
async def test_ops_service_brief_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/service-brief/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-service-brief-v1"
    assert "runtime" in body["required_fields"]
    assert "llm_provider" in body["runtime_required_fields"]
    assert "deployment" in body["stage_keys"]
