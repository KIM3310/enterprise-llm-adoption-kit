from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import create_jwt
from app.main import app


token = create_jwt(user_id="ops-runtime-script", role="Admin")


async def main() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/ops/runtime/scorecard",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        body = response.json()
    print(
        json.dumps(
            {
                "ok": True,
                "contract_version": body["contract_version"],
                "startup_status": body["summary"]["startup_status"],
                "request_count": body["summary"]["request_count"],
                "alert_count": body["summary"]["alert_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    import anyio

    anyio.run(main)
