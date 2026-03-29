from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = REPO_ROOT / "docs" / "datadog" / "assets"

DD_SITE = os.environ.get("DD_SITE", "datadoghq.com").strip()
DD_API_KEY = os.environ.get("DD_API_KEY", "").strip()
DD_APP_KEY = os.environ.get("DD_APP_KEY", "").strip()
DD_SERVICE = os.environ.get("DD_SERVICE", "enterprise-llm-adoption-kit").strip()
DD_ENV = os.environ.get("DD_ENV", "production").strip()
DD_DASHBOARD_PREFIX = os.environ.get("DD_DASHBOARD_PREFIX", "Portfolio").strip()


def _apply_templates(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        for key, replacement in replacements.items():
            value = value.replace(f"{{{{{key}}}}}", replacement)
        return value
    if isinstance(value, list):
        return [_apply_templates(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _apply_templates(item, replacements) for key, item in value.items()}
    return value


def _load_assets() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    replacements = {
        "PREFIX": DD_DASHBOARD_PREFIX,
        "SERVICE": DD_SERVICE,
        "ENV": DD_ENV,
    }
    dashboard = json.loads((ASSET_DIR / "dashboard.json").read_text())
    monitors = json.loads((ASSET_DIR / "monitors.json").read_text())
    return _apply_templates(dashboard, replacements), _apply_templates(monitors, replacements)


def _datadog_request(method: str, api_path: str, payload: Any | None = None, *, require_app_key: bool = True) -> Any:
    if not DD_API_KEY:
        raise RuntimeError("DD_API_KEY is required for Datadog API calls.")
    if require_app_key and not DD_APP_KEY:
        raise RuntimeError("DD_APP_KEY is required for dashboard and monitor sync.")

    request = urllib.request.Request(
        url=f"https://api.{DD_SITE}{api_path}",
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "DD-API-KEY": DD_API_KEY,
            **({"DD-APPLICATION-KEY": DD_APP_KEY} if require_app_key else {}),
        },
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
    )

    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {api_path} failed ({exc.code}): {body}") from exc


def validate_credentials() -> dict[str, Any]:
    if not DD_API_KEY:
        return {"apiKeyValid": False, "appKeyConfigured": bool(DD_APP_KEY), "skipped": True}

    result = _datadog_request("GET", "/api/v1/validate", require_app_key=False)
    return {
        "apiKeyValid": bool(result.get("valid")),
        "appKeyConfigured": bool(DD_APP_KEY),
    }


def sync_assets() -> dict[str, Any]:
    dashboard, monitors = _load_assets()
    dashboards = _datadog_request("GET", "/api/v1/dashboard")
    existing_dashboard = next(
        (item for item in dashboards.get("dashboards", []) if item.get("title") == dashboard["title"]),
        None,
    )
    if existing_dashboard:
        dashboard_result = _datadog_request("PUT", f"/api/v1/dashboard/{existing_dashboard['id']}", dashboard)
        dashboard_mode = "updated"
    else:
        dashboard_result = _datadog_request("POST", "/api/v1/dashboard", dashboard)
        dashboard_mode = "created"

    existing_monitors = _datadog_request("GET", "/api/v1/monitor")
    synced_monitors = []
    for monitor in monitors:
        existing = next((item for item in existing_monitors if item.get("name") == monitor["name"]), None)
        if existing:
            monitor_result = _datadog_request("PUT", f"/api/v1/monitor/{existing['id']}", monitor)
            monitor_mode = "updated"
        else:
            monitor_result = _datadog_request("POST", "/api/v1/monitor", monitor)
            monitor_mode = "created"
        synced_monitors.append(
            {
                "id": monitor_result.get("id"),
                "name": monitor_result.get("name", monitor["name"]),
                "mode": monitor_mode,
            }
        )

    return {
        "dashboard": {
            "id": dashboard_result.get("id"),
            "title": dashboard_result.get("title", dashboard["title"]),
            "mode": dashboard_mode,
        },
        "monitors": synced_monitors,
    }


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    dashboard, monitors = _load_assets()

    if mode == "plan":
        print(
            json.dumps(
                {
                    "site": DD_SITE,
                    "service": DD_SERVICE,
                    "env": DD_ENV,
                    "prefix": DD_DASHBOARD_PREFIX,
                    "dashboard": dashboard["title"],
                    "monitors": [monitor["name"] for monitor in monitors],
                    "credentials": {
                        "apiKeyConfigured": bool(DD_API_KEY),
                        "appKeyConfigured": bool(DD_APP_KEY),
                    },
                },
                indent=2,
            )
        )
        return

    if mode == "validate":
        print(json.dumps(validate_credentials(), indent=2))
        return

    if mode == "sync":
        print(json.dumps(validate_credentials(), indent=2))
        print(json.dumps(sync_assets(), indent=2))
        return

    raise SystemExit(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    main()
