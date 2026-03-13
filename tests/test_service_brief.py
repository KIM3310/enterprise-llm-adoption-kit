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
    assert body["links"]["review_pack"] == "/ops/review-pack"
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"
    assert body["links"]["review_summary"] == "/ops/review-summary"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"
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


@pytest.mark.anyio
async def test_ops_review_pack_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-pack")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-review-pack-v1"
    assert body["runtime_summary"]["llm_provider"] == "stub"
    assert body["proof_bundle"]["tests"] >= 20
    assert body["proof_bundle"]["review_assets_count"] >= 4
    assert "/ops/rollout-board" in body["proof_bundle"]["runtime_surfaces"]
    assert "/ops/rollout-drill" in body["proof_bundle"]["runtime_surfaces"]
    assert "/ops/review-summary" in body["proof_bundle"]["runtime_surfaces"]
    assert "/ops/runtime/scorecard" in body["proof_bundle"]["runtime_surfaces"]
    assert "/ops/review-pack/schema" in body["proof_bundle"]["runtime_surfaces"]
    assert any(item["label"] == "Inspect executive overview" for item in body["review_actions"])
    assert len(body["two_minute_review"]) == 4
    assert body["review_gate"]["status"] in {"ready", "attention"}
    assert body["review_gate"]["next_step"]
    assert any("snowflake" in item for item in body["platform_dialogues"])
    assert body["links"]["review_pack"] == "/ops/review-pack"
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"
    assert body["links"]["review_summary"] == "/ops/review-summary"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"
    assert body["links"]["review_pack_schema"] == "/ops/review-pack/schema"


@pytest.mark.anyio
async def test_ops_review_pack_flags_degraded_runtime_posture(monkeypatch) -> None:
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "startup_status", "degraded", raising=False)
    monkeypatch.setattr(main_module.settings, "llm_circuit_state", "open", raising=False)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-pack")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["review_gate"]["status"] == "attention"
    assert "startup" in body["review_gate"]["blocker"].lower() or "circuit" in body["review_gate"]["blocker"].lower()
    assert "/ops/runtime/scorecard" in body["review_gate"]["next_step"]


@pytest.mark.anyio
async def test_ops_review_pack_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-pack/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-review-pack-v1"
    assert "review_actions" in body["required_fields"]
    assert "two_minute_review" in body["required_fields"]
    assert "review_assets" in body["proof_bundle_required_fields"]
    assert "surface" in body["review_action_required_fields"]
    assert "step" in body["two_minute_review_required_fields"]


@pytest.mark.anyio
async def test_ops_review_summary_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-summary?stage=operations")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-review-summary-v1"
    assert body["readiness"]["focus_stage"] == "operations"
    assert body["readiness"]["ready_stage_count"] + body["readiness"]["attention_stage_count"] >= 1
    assert body["coverage"]["tests"] >= 20
    assert body["stage_highlights"][0]["key"] == "operations"
    assert isinstance(body["fastest_review_path"], list)
    assert len(body["fastest_review_path"]) == 3
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["review_summary"] == "/ops/review-summary"


@pytest.mark.anyio
async def test_ops_rollout_board_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-board?track=hybrid%20control%20tower")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-rollout-board-v1"
    assert body["filters"]["track"] == "hybrid control tower"
    assert body["summary"]["visible_tracks"] == 1
    assert body["items"][0]["track"] == "hybrid control tower"
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"


@pytest.mark.anyio
async def test_ops_rollout_board_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-board/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-rollout-board-v1"
    assert "summary" in body["required_fields"]
    assert "items" in body["required_fields"]
    assert "track" in body["item_required_fields"]
    assert body["links"]["rollout_board"] == "/ops/rollout-board"


@pytest.mark.anyio
async def test_ops_rollout_drill_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-drill?track=hybrid%20control%20tower")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-rollout-drill-v1"
    assert body["filters"]["track"] == "hybrid control tower"
    assert body["summary"]["visible_tracks"] == 1
    assert body["items"][0]["track"] == "hybrid control tower"
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"


@pytest.mark.anyio
async def test_ops_rollout_drill_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-drill/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-rollout-drill-v1"
    assert "summary" in body["required_fields"]
    assert "items" in body["required_fields"]
    assert "rollback_eta_minutes" in body["item_required_fields"]
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"


@pytest.mark.anyio
async def test_ops_review_summary_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-summary/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-review-summary-v1"
    assert "readiness" in body["required_fields"]
    assert "coverage" in body["required_fields"]
    assert "stage_highlights" in body["required_fields"]
    assert "top_assets" in body["required_fields"]
    assert "maturity_stage" in body["readiness_required_fields"]
    assert "focus_stage" in body["readiness_required_fields"]
    assert "tests" in body["coverage_required_fields"]


@pytest.mark.anyio
async def test_ops_review_summary_rejects_invalid_stage_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/review-summary?stage=bad-stage")

    assert response.status_code == 400, response.text
    assert "invalid stage filter" in response.json()["detail"]


@pytest.mark.anyio
async def test_ops_rollout_board_rejects_invalid_track_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-board?track=bad-track")

    assert response.status_code == 400, response.text
    assert "invalid stage filter" in response.json()["detail"]
