import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATADOG_ASSETS_PATH = REPO_ROOT / "scripts" / "datadog_assets.py"


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps({"valid": True}).encode("utf-8")


def _load_datadog_assets(monkeypatch, site: str):
    monkeypatch.setenv("DD_SITE", site)
    monkeypatch.setenv("DD_API_KEY", "test-api-key")
    monkeypatch.delenv("DD_APP_KEY", raising=False)
    module_name = "datadog_assets_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, DATADOG_ASSETS_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("site", "expected_url"),
    [
        ("datadoghq.com", "https://api.datadoghq.com/api/v1/validate"),
        ("us3.datadoghq.com", "https://api.us3.datadoghq.com/api/v1/validate"),
        ("us5.datadoghq.com", "https://api.us5.datadoghq.com/api/v1/validate"),
        ("datadoghq.eu", "https://api.datadoghq.eu/api/v1/validate"),
        ("ap1.datadoghq.com", "https://api.ap1.datadoghq.com/api/v1/validate"),
        ("ap2.datadoghq.com", "https://api.ap2.datadoghq.com/api/v1/validate"),
        ("ddog-gov.com", "https://api.ddog-gov.com/api/v1/validate"),
    ],
)
def test_datadog_request_accepts_documented_sites(monkeypatch, site: str, expected_url: str) -> None:
    datadog_assets = _load_datadog_assets(monkeypatch, site)
    captured = {}

    def _fake_urlopen(request):
        captured["url"] = request.full_url
        return _FakeResponse()

    monkeypatch.setattr(datadog_assets.urllib.request, "urlopen", _fake_urlopen)

    assert datadog_assets.validate_credentials()["apiKeyValid"] is True
    assert captured["url"] == expected_url


def test_datadog_request_rejects_userinfo_exfiltration_site_before_urlopen(monkeypatch) -> None:
    datadog_assets = _load_datadog_assets(monkeypatch, "datadoghq.com@evil.example")

    def _fake_urlopen(request):
        raise AssertionError(f"urlopen should not be called for {request.full_url}")

    monkeypatch.setattr(datadog_assets.urllib.request, "urlopen", _fake_urlopen)

    with pytest.raises(RuntimeError, match="Unsupported DD_SITE"):
        datadog_assets.validate_credentials()


@pytest.mark.parametrize(
    "site",
    [
        "https://datadoghq.com",
        "datadoghq.com:443",
        "datadoghq.com/api/v1/validate",
        "datadoghq..com",
    ],
)
def test_datadog_request_rejects_malformed_site_values_before_urlopen(monkeypatch, site: str) -> None:
    datadog_assets = _load_datadog_assets(monkeypatch, site)

    def _fake_urlopen(request):
        raise AssertionError(f"urlopen should not be called for {request.full_url}")

    monkeypatch.setattr(datadog_assets.urllib.request, "urlopen", _fake_urlopen)

    with pytest.raises(RuntimeError, match="Unsupported DD_SITE"):
        datadog_assets.validate_credentials()
