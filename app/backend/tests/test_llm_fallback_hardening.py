import pytest
from fastapi import HTTPException

import app.main as main_module


class _FailingAdapter:
    def generate(self, messages, use_case):
        raise RuntimeError("provider unavailable")


def test_call_llm_falls_back_to_stub_when_provider_fails(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(main_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module, "get_llm_adapter", lambda: _FailingAdapter())
    monkeypatch.setattr(
        main_module,
        "get_llm_runtime_settings",
        lambda: {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 512,
            "openai_api_key_configured": False,
        },
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        type(
            "SettingsProxy",
            (),
            {
                "llm_fallback_to_stub_on_error": True,
            },
        )(),
    )
    recorded = {}

    def _capture_event(*, level, component, message, context):
        recorded["level"] = level
        recorded["component"] = component
        recorded["message"] = message
        recorded["context"] = context

    monkeypatch.setattr(main_module, "_safe_record_service_event", _capture_event)

    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "Summarize architecture risks."},
        {"role": "assistant", "content": "CONTEXT:\n[ARC-1001:summary] payments risk"},
    ]
    result = main_module._call_llm_with_retry(messages, use_case="uc1")

    assert isinstance(result.text, str) and result.text.strip()
    assert recorded["component"] == "llm_adapter"
    assert recorded["level"] == "WARN"


def test_call_llm_raises_when_stub_provider_fails(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "LLM_MAX_RETRIES", 1)
    monkeypatch.setattr(main_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main_module, "get_llm_adapter", lambda: _FailingAdapter())
    monkeypatch.setattr(
        main_module,
        "get_llm_runtime_settings",
        lambda: {
            "provider": "stub",
            "model": "stub-llm",
            "temperature": 0.2,
            "max_tokens": 512,
            "openai_api_key_configured": False,
        },
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        type(
            "SettingsProxy",
            (),
            {
                "llm_fallback_to_stub_on_error": True,
            },
        )(),
    )

    with pytest.raises(HTTPException) as exc:
        main_module._call_llm_with_retry([{"role": "user", "content": "hi"}], use_case="uc1")
    assert exc.value.status_code == 502
