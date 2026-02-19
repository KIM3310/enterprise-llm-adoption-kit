import time

import httpx
import pytest
from fastapi import HTTPException

import app.main as main_module
from app.llm_adapter import LLMResult
from app.rate_limit import RateLimiter


class _SettingsProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


@pytest.mark.anyio
async def test_login_rate_limit_blocks_repeated_invalid_code(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, demo_login_code="atelier-2026"),
    )
    monkeypatch.setattr(
        main_module,
        "login_attempt_limiter",
        RateLimiter(capacity=2, refill_per_sec=0.0001),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post(
            "/auth/login",
            json={"user_id": "demo-user", "role": "Employee", "login_code": "wrong"},
        )
        second = await client.post(
            "/auth/login",
            json={"user_id": "demo-user", "role": "Employee", "login_code": "wrong"},
        )
        third = await client.post(
            "/auth/login",
            json={"user_id": "demo-user", "role": "Employee", "login_code": "wrong"},
        )

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429
    assert third.json().get("detail") == "Too many login attempts. Retry later."


@pytest.mark.anyio
async def test_login_rate_limit_not_used_when_login_code_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(main_module.settings, demo_login_code=""),
    )
    monkeypatch.setattr(
        main_module,
        "login_attempt_limiter",
        RateLimiter(capacity=1, refill_per_sec=0.0001),
    )

    transport = httpx.ASGITransport(app=main_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(3):
            response = await client.post(
                "/auth/login",
                json={"user_id": "demo-user", "role": "Employee"},
            )
            assert response.status_code == 200, response.text


class _FailingAdapter:
    def generate(self, messages, use_case):
        raise RuntimeError("provider unavailable")


class _SuccessAdapter:
    def generate(self, messages, use_case):
        return LLMResult(text="ok", tokens_in=1, tokens_out=1, cost=0.0)


def _set_circuit_state(monkeypatch, *, failures: int, open_until: float) -> None:
    monkeypatch.setattr(main_module, "LLM_CIRCUIT_CONSECUTIVE_FAILURES", failures)
    monkeypatch.setattr(main_module, "LLM_CIRCUIT_OPEN_UNTIL", open_until)
    monkeypatch.setattr(main_module, "LLM_CIRCUIT_LAST_ERROR", "")


def test_llm_circuit_returns_stub_without_calling_provider_when_open(monkeypatch) -> None:
    _set_circuit_state(monkeypatch, failures=5, open_until=time.time() + 60)
    called = {"value": False}

    def _unexpected_adapter():
        called["value"] = True
        return _FailingAdapter()

    monkeypatch.setattr(main_module, "get_llm_adapter", _unexpected_adapter)
    monkeypatch.setattr(
        main_module,
        "get_llm_runtime_settings",
        lambda: {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 512,
            "openai_api_key_configured": True,
        },
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(
            main_module.settings,
            llm_fallback_to_stub_on_error=True,
            llm_circuit_breaker_threshold=2,
            llm_circuit_breaker_cooldown_sec=30,
        ),
    )

    result = main_module._call_llm_with_retry(
        [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Summarize architecture risks."},
            {"role": "assistant", "content": "CONTEXT:\n[ARC-1001:summary] payments risk"},
        ],
        use_case="uc1",
    )

    assert isinstance(result.text, str) and result.text.strip()
    assert called["value"] is False


def test_llm_circuit_opens_after_repeated_failures(monkeypatch) -> None:
    _set_circuit_state(monkeypatch, failures=0, open_until=0.0)
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
            "openai_api_key_configured": True,
        },
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(
            main_module.settings,
            llm_fallback_to_stub_on_error=False,
            llm_circuit_breaker_threshold=2,
            llm_circuit_breaker_cooldown_sec=60,
        ),
    )

    with pytest.raises(HTTPException) as first_exc:
        main_module._call_llm_with_retry([{"role": "user", "content": "hi"}], use_case="uc1")
    assert first_exc.value.status_code == 502

    snap1 = main_module._llm_circuit_snapshot()
    assert snap1["state"] == "closed"
    assert snap1["consecutive_failures"] == 1

    with pytest.raises(HTTPException) as second_exc:
        main_module._call_llm_with_retry([{"role": "user", "content": "hi"}], use_case="uc1")
    assert second_exc.value.status_code == 502
    assert second_exc.value.detail == "LLM call failed after retries"

    snap2 = main_module._llm_circuit_snapshot()
    assert snap2["state"] == "open"
    assert snap2["consecutive_failures"] >= 2
    assert snap2["open_seconds_remaining"] > 0


def test_llm_circuit_resets_on_successful_provider_call(monkeypatch) -> None:
    _set_circuit_state(monkeypatch, failures=2, open_until=0.0)
    monkeypatch.setattr(main_module, "get_llm_adapter", lambda: _SuccessAdapter())
    monkeypatch.setattr(
        main_module,
        "get_llm_runtime_settings",
        lambda: {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 512,
            "openai_api_key_configured": True,
        },
    )
    monkeypatch.setattr(
        main_module,
        "settings",
        _SettingsProxy(
            main_module.settings,
            llm_fallback_to_stub_on_error=False,
            llm_circuit_breaker_threshold=2,
            llm_circuit_breaker_cooldown_sec=60,
        ),
    )

    result = main_module._call_llm_with_retry([{"role": "user", "content": "hi"}], use_case="uc1")
    assert result.text == "ok"

    snap = main_module._llm_circuit_snapshot()
    assert snap["state"] == "closed"
    assert snap["consecutive_failures"] == 0
