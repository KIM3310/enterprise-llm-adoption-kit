import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "app" / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "enterprise-llm-test-secret")

from app.llm_adapter import reset_llm_runtime_settings, update_llm_runtime_settings
import app.main as main_module


class _SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


@pytest.fixture(autouse=True)
def _force_stub_llm_runtime(monkeypatch) -> None:
    # Keep tests hermetic even when the shell has provider/API key variables set.
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, demo_login_code=""),
    )
    update_llm_runtime_settings(provider="stub", openai_api_key="")
    yield
    reset_llm_runtime_settings()
