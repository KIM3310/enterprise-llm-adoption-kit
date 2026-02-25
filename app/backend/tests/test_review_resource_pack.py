import httpx
import pytest

from app.main import app
from app.review_resource_pack import data_files, resource_pack_summary


@pytest.mark.anyio
async def test_review_resource_pack_endpoint_exposes_built_in_assets() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ops/resource-pack")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["contract_version"] == "enterprise-adoption-review-resource-pack-v1"
    assert payload["summary"]["scenario_count"] >= 4
    assert payload["reviewer_fast_path"][2] == "/ops/resource-pack"
    assert "preview_rows" in payload["external_data"]


def test_review_resource_pack_files_exist() -> None:
    for path in data_files().values():
        assert path.exists()
    assert resource_pack_summary()["playbook_count"] >= 3
