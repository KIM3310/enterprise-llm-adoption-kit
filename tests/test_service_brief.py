import httpx
import pytest
import time

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
    assert body["runtime"]["deploymentMode"] == "read-only-live"
    assert body["evidence"]["test_files"] >= 20
    assert "aws" in body["platform_targets"]
    assert len(body["role_paths"]) >= 3
    assert any(item["role"] == "Operator" for item in body["role_paths"])
    assert body["links"]["proof_map"] == "docs/architecture/llm_deployment_options.md"
    assert body["links"]["customer_architecture_pack"] == "/ops/customer-architecture-pack"
    assert body["links"]["summary_pack"] == "/ops/summary-pack"
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"
    assert body["links"]["rollout_gates"] == "/ops/rollout-gates"
    assert body["links"]["architecture_summary"] == "/ops/architecture-summary"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"
    assert body["links"]["service_brief_schema"] == "/ops/service-brief/schema"
    assert body["links"]["resource_pack"] == "/ops/resource-pack"
    assert body["links"]["platform_proof_board"] == "/ops/platform-proof-board"
    assert body["links"]["workshop_readout_pack"] == "/ops/workshop-readout-pack"
    assert body["links"]["workshop_readout_pack_schema"] == "/ops/workshop-readout-pack/schema"
    assert body["links"]["live_workshop_preview"] == "/ops/live-workshop-preview"
    assert any(stage["key"] == "operations" for stage in body["stages"])
    assert any(step["endpoint"] == "/auth/login" for step in body["architecture_flow"])


@pytest.mark.anyio
async def test_ops_service_brief_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/service-brief/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-service-brief-v1"
    assert "runtime" in body["required_fields"]
    assert "role_paths" in body["required_fields"]
    assert "llm_provider" in body["runtime_required_fields"]
    assert "proof_assets" in body["role_path_required_fields"]
    assert "deployment" in body["stage_keys"]


@pytest.mark.anyio
async def test_ops_summary_pack_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/summary-pack")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-summary-pack-v1"
    assert body["runtime_summary"]["llm_provider"] == "stub"
    assert body["evidence_bundle"]["tests"] >= 20
    assert body["evidence_bundle"]["architecture_assets_count"] >= 4
    assert len(body["role_paths"]) >= 3
    assert any(item["role"] == "Solution Architect" for item in body["role_paths"])
    assert "/ops/rollout-board" in body["evidence_bundle"]["runtime_surfaces"]
    assert "/ops/rollout-drill" in body["evidence_bundle"]["runtime_surfaces"]
    assert "/ops/rollout-gates" in body["evidence_bundle"]["runtime_surfaces"]
    assert "/ops/architecture-summary" in body["evidence_bundle"]["runtime_surfaces"]
    assert "/ops/runtime/scorecard" in body["evidence_bundle"]["runtime_surfaces"]
    assert "/ops/summary-pack/schema" in body["evidence_bundle"]["runtime_surfaces"]
    assert any(item["label"] == "Inspect executive overview" for item in body["architecture_actions"])
    assert len(body["two_minute_architecture"]) == 5
    assert body["architecture_gate"]["status"] in {"ready", "attention"}
    assert body["architecture_gate"]["next_step"]
    assert any("snowflake" in item for item in body["platform_dialogues"])
    assert body["evidence_bundle"]["resource_pack"]["scenario_count"] >= 4
    assert "/ops/resource-pack" in body["evidence_bundle"]["runtime_surfaces"]
    assert body["links"]["summary_pack"] == "/ops/summary-pack"
    assert body["links"]["resource_pack"] == "/ops/resource-pack"
    assert body["links"]["customer_architecture_pack"] == "/ops/customer-architecture-pack"
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["rollout_drill"] == "/ops/rollout-drill"
    assert body["links"]["rollout_gates"] == "/ops/rollout-gates"
    assert body["links"]["architecture_summary"] == "/ops/architecture-summary"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"
    assert body["links"]["summary_pack_schema"] == "/ops/summary-pack/schema"
    assert body["links"]["proof_map"] == "docs/architecture/llm_deployment_options.md"


@pytest.mark.anyio
async def test_ops_platform_proof_board_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/platform-proof-board")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-platform-proof-board-v1"
    assert "openai" in body["platforms"]
    assert "bedrock" in body["platforms"]
    assert "snowflake" in body["platforms"]
    assert "databricks" in body["platforms"]
    assert body["links"]["service_brief"] == "/ops/service-brief"


@pytest.mark.anyio
async def test_ops_customer_architecture_pack_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/customer-architecture-pack?platform=snowflake")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-customer-architecture-pack-v1"
    assert body["filters"]["platform"] == "snowflake"
    assert body["summary"]["visible_platforms"] == 1
    assert body["platform_cards"][0]["platform"] == "snowflake"
    assert len(body["architecture_stages"]) == 5
    assert body["links"]["customer_architecture_pack"] == "/ops/customer-architecture-pack"
    assert body["links"]["summary_pack"] == "/ops/summary-pack"


@pytest.mark.anyio
async def test_ops_customer_architecture_pack_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/customer-architecture-pack/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-customer-architecture-pack-v1"
    assert "summary" in body["required_fields"]
    assert "platform_cards" in body["required_fields"]
    assert "platform" in body["platform_card_required_fields"]
    assert body["links"]["customer_architecture_pack"] == "/ops/customer-architecture-pack"


@pytest.mark.anyio
async def test_ops_workshop_readout_pack_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/workshop-readout-pack?platform=snowflake")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-workshop-readout-pack-v1"
    assert body["filters"]["platform"] == "snowflake"
    assert body["summary"]["decision_stage_count"] == 5
    assert body["summary"]["visual_evidence_count"] >= 2
    assert len(body["decision_log"]) == 5
    assert any(item["kind"] == "image" for item in body["visual_evidence"])
    assert body["links"]["workshop_readout_pack"] == "/ops/workshop-readout-pack"
    assert body["links"]["customer_architecture_pack"] == "/ops/customer-architecture-pack"
    assert body["links"]["workshop_visual"] == "docs/architecture_assets/demo_screenshots/15_workshop_readout.svg"


@pytest.mark.anyio
async def test_ops_live_workshop_preview_contract(monkeypatch) -> None:
    import app.main as main_module

    monkeypatch.setenv("OPENAI_API_KEY", "sk-enterprise-live")

    async def _fake_moderation(api_key: str, payload: str) -> None:
        assert api_key == "sk-enterprise-live"
        assert "snowflake-discovery" in payload

    async def _fake_preview(api_key: str, model: str, payload: dict) -> dict:
        assert api_key == "sk-enterprise-live"
        assert model == "gpt-4o-mini"
        assert payload["scenario"]["platform"] == "snowflake"
        return {
            "rolloutStance": "pilot-now",
            "executiveSummary": "Governed Snowflake workshop is ready for a bounded pilot.",
            "architectureSummary": "Keep rollout gates and summary pack visible during stakeholder handoff.",
            "nextAction": "open customer architecture pack",
            "proofAssets": ["/ops/workshop-readout-pack", "/ops/customer-architecture-pack"],
        }

    monkeypatch.setattr(main_module, "_call_openai_moderation", _fake_moderation)
    monkeypatch.setattr(main_module, "_call_openai_workshop_preview", _fake_preview)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/ops/live-workshop-preview",
            json={"scenario_id": "snowflake-discovery"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-live-workshop-preview-v1"
    assert body["mode"] == "public-capped-live"
    assert body["model"] == "gpt-4o-mini"
    assert body["scenarioId"] == "snowflake-discovery"
    assert body["nextArchitecturePath"] == "/ops/customer-architecture-pack?platform=snowflake"
    assert body["result"]["platform"] == "snowflake"
    assert body["result"]["rolloutStance"] == "pilot-now"


@pytest.mark.anyio
async def test_ops_workshop_readout_pack_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/workshop-readout-pack/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-workshop-readout-pack-v1"
    assert "decision_log" in body["required_fields"]
    assert "visual_evidence" in body["required_fields"]
    assert "decision_stage_count" in body["summary_required_fields"]
    assert "stage" in body["decision_log_required_fields"]
    assert body["links"]["workshop_readout_pack"] == "/ops/workshop-readout-pack"


@pytest.mark.anyio
async def test_ops_summary_pack_flags_degraded_runtime_posture(monkeypatch) -> None:
    import app.main as main_module

    monkeypatch.setattr(
        app.state,
        "startup_report",
        {
            "startup_ready": False,
            "overall_status": "degraded",
            "failed_checks": ["runbooks"],
        },
        raising=False,
    )
    monkeypatch.setattr(main_module, "LLM_CIRCUIT_CONSECUTIVE_FAILURES", 3)
    monkeypatch.setattr(main_module, "LLM_CIRCUIT_OPEN_UNTIL", time.time() + 60)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/summary-pack")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["architecture_gate"]["status"] == "attention"
    assert "startup" in body["architecture_gate"]["blocker"].lower() or "circuit" in body["architecture_gate"]["blocker"].lower()
    assert "/ops/runtime/scorecard" in body["architecture_gate"]["next_step"]


@pytest.mark.anyio
async def test_ops_summary_pack_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/summary-pack/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-summary-pack-v1"
    assert "architecture_actions" in body["required_fields"]
    assert "two_minute_architecture" in body["required_fields"]
    assert "role_paths" in body["required_fields"]
    assert "architecture_assets" in body["evidence_bundle_required_fields"]
    assert "surface" in body["architecture_action_required_fields"]
    assert "step" in body["two_minute_architecture_required_fields"]
    assert "proof_assets" in body["role_path_required_fields"]


@pytest.mark.anyio
async def test_ops_architecture_summary_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/architecture-summary?stage=operations")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-architecture-summary-v1"
    assert body["readiness"]["focus_stage"] == "operations"
    assert body["readiness"]["ready_stage_count"] + body["readiness"]["attention_stage_count"] >= 1
    assert body["coverage"]["tests"] >= 20
    assert body["stage_highlights"][0]["key"] == "operations"
    assert isinstance(body["fastest_architecture_path"], list)
    assert len(body["fastest_architecture_path"]) == 3
    assert body["links"]["rollout_board"] == "/ops/rollout-board"
    assert body["links"]["architecture_summary"] == "/ops/architecture-summary"


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
async def test_ops_rollout_gates_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-gates?track=hybrid%20control%20tower")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract_version"] == "enterprise-adoption-rollout-gates-v1"
    assert body["filters"]["track"] == "hybrid control tower"
    assert body["summary"]["visible_tracks"] == 1
    assert body["summary"]["total_gates"] == 4
    assert body["summary"]["release_recommendation"] in {"proceed", "hold"}
    assert body["tracks"][0]["track"] == "hybrid control tower"
    assert len(body["gates"]) == 4
    assert any(item["gate"] == "runtime-readiness" for item in body["gates"])
    assert any(item["gate"] == "rollback-drill" for item in body["gates"])
    assert body["links"]["rollout_gates"] == "/ops/rollout-gates"
    assert body["links"]["ops_runtime_scorecard"] == "/ops/runtime/scorecard"


@pytest.mark.anyio
async def test_ops_rollout_gates_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-gates/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-rollout-gates-v1"
    assert "summary" in body["required_fields"]
    assert "gates" in body["required_fields"]
    assert "gate_label" in body["gate_required_fields"]
    assert body["links"]["rollout_gates"] == "/ops/rollout-gates"


@pytest.mark.anyio
async def test_ops_architecture_summary_schema_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/architecture-summary/schema")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema"] == "enterprise-adoption-architecture-summary-v1"
    assert "readiness" in body["required_fields"]
    assert "coverage" in body["required_fields"]
    assert "stage_highlights" in body["required_fields"]
    assert "top_assets" in body["required_fields"]
    assert "maturity_stage" in body["readiness_required_fields"]
    assert "focus_stage" in body["readiness_required_fields"]
    assert "tests" in body["coverage_required_fields"]


@pytest.mark.anyio
async def test_ops_architecture_summary_rejects_invalid_stage_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/architecture-summary?stage=bad-stage")

    assert response.status_code == 400, response.text
    assert "invalid stage filter" in response.json()["detail"]


@pytest.mark.anyio
async def test_ops_rollout_board_rejects_invalid_track_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-board?track=bad-track")

    assert response.status_code == 400, response.text
    assert "invalid stage filter" in response.json()["detail"]


@pytest.mark.anyio
async def test_ops_rollout_gates_rejects_invalid_track_filter() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ops/rollout-gates?track=bad-track")

    assert response.status_code == 400, response.text
    assert "invalid stage filter" in response.json()["detail"]
