from dataclasses import dataclass
from threading import Lock
from typing import Dict, List, Optional

import requests

from .config import settings


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    cost: float


RUNTIME_PROVIDER_OPTIONS = {"stub", "openai", "openai_compatible"}

_runtime_lock = Lock()
_runtime_overrides: Dict[str, Optional[object]] = {
    "provider": None,
    "model": None,
    "temperature": None,
    "max_tokens": None,
    "timeout_sec": None,
    "openai_base_url": None,
    "openai_org": None,
    "openai_api_key": None,
}


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _estimate_cost(tokens_in: int, tokens_out: int) -> float:
    cost_in = (tokens_in / 1000.0) * settings.cost_per_1k_input_tokens
    cost_out = (tokens_out / 1000.0) * settings.cost_per_1k_output_tokens
    return round(cost_in + cost_out, 6)


class LLMAdapter:
    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        raise NotImplementedError


def _normalize_provider(value: str) -> str:
    provider = str(value or "stub").strip().lower()
    if provider not in RUNTIME_PROVIDER_OPTIONS:
        raise ValueError(f"provider must be one of {sorted(RUNTIME_PROVIDER_OPTIONS)}")
    return provider


def _active_runtime_config() -> Dict[str, object]:
    with _runtime_lock:
        provider_raw = _runtime_overrides["provider"]
        model_raw = _runtime_overrides["model"]
        temperature_raw = _runtime_overrides["temperature"]
        max_tokens_raw = _runtime_overrides["max_tokens"]
        timeout_raw = _runtime_overrides["timeout_sec"]
        base_url_raw = _runtime_overrides["openai_base_url"]
        org_raw = _runtime_overrides["openai_org"]
        api_key_raw = _runtime_overrides["openai_api_key"]

    provider = _normalize_provider(str(provider_raw or settings.llm_provider or "stub"))
    model = str(model_raw or settings.llm_model).strip()
    if not model:
        model = "stub-llm"
    temperature = float(
        settings.llm_temperature if temperature_raw is None else temperature_raw
    )
    max_tokens = int(settings.llm_max_tokens if max_tokens_raw is None else max_tokens_raw)
    timeout_sec = float(settings.llm_timeout_sec if timeout_raw is None else timeout_raw)
    base_url = str(base_url_raw or settings.llm_openai_base_url).strip()
    org = str(org_raw or settings.llm_openai_org).strip()
    api_key = str(api_key_raw or settings.llm_openai_api_key).strip()

    return {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout_sec": timeout_sec,
        "openai_base_url": base_url,
        "openai_org": org,
        "openai_api_key": api_key,
    }


def get_llm_runtime_settings() -> Dict[str, object]:
    config = _active_runtime_config()
    api_key = str(config.pop("openai_api_key", "")).strip()
    config["openai_api_key_configured"] = bool(api_key)
    return config


def reset_llm_runtime_settings() -> Dict[str, object]:
    with _runtime_lock:
        for key in _runtime_overrides:
            _runtime_overrides[key] = None
    return get_llm_runtime_settings()


def update_llm_runtime_settings(
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout_sec: Optional[float] = None,
    openai_base_url: Optional[str] = None,
    openai_org: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    reset_to_env: bool = False,
) -> Dict[str, object]:
    if reset_to_env:
        return reset_llm_runtime_settings()

    with _runtime_lock:
        if provider is not None:
            _runtime_overrides["provider"] = _normalize_provider(provider)
        if model is not None:
            model_value = str(model).strip()
            if not model_value:
                raise ValueError("model cannot be empty")
            _runtime_overrides["model"] = model_value
        if temperature is not None:
            _runtime_overrides["temperature"] = float(temperature)
        if max_tokens is not None:
            _runtime_overrides["max_tokens"] = int(max_tokens)
        if timeout_sec is not None:
            _runtime_overrides["timeout_sec"] = float(timeout_sec)
        if openai_base_url is not None:
            _runtime_overrides["openai_base_url"] = str(openai_base_url).strip()
        if openai_org is not None:
            _runtime_overrides["openai_org"] = str(openai_org).strip()
        if openai_api_key is not None:
            _runtime_overrides["openai_api_key"] = str(openai_api_key).strip()

    return get_llm_runtime_settings()


class OpenAICompatibleAdapter(LLMAdapter):
    def __init__(self) -> None:
        runtime = _active_runtime_config()
        self.base_url = str(runtime["openai_base_url"]).rstrip("/")
        self.api_key = str(runtime["openai_api_key"]).strip()
        self.organization = str(runtime["openai_org"]).strip()
        self.timeout_sec = max(1.0, float(runtime["timeout_sec"]))
        self.model = str(runtime["model"])
        self.temperature = float(runtime["temperature"])
        self.max_tokens = int(runtime["max_tokens"])

    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        if not self.api_key:
            raise RuntimeError("LLM_OPENAI_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("OpenAI-compatible response is not valid JSON") from exc

        text = _extract_response_text(data)
        usage = data.get("usage", {}) if isinstance(data, dict) else {}
        tokens_in = int(usage.get("prompt_tokens") or _estimate_tokens(" ".join([m["content"] for m in messages])))
        tokens_out = int(usage.get("completion_tokens") or _estimate_tokens(text))
        cost = _estimate_cost(tokens_in, tokens_out)
        return LLMResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)


class StubLLMAdapter(LLMAdapter):
    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        # Deterministic stub output based on last user message
        _ = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if use_case == "uc1":
            response = (
                "Architecture validation summary based on retrieved governance context. "
                "Priority risks and next actions are listed."
            )
        else:
            response = (
                "Log summary: errors detected with likely root causes. "
                "Runbook steps recommended."
            )
        tokens_in = _estimate_tokens(" ".join([m["content"] for m in messages]))
        tokens_out = _estimate_tokens(response)
        cost = _estimate_cost(tokens_in, tokens_out)
        return LLMResult(text=response, tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)


def _extract_response_text(data: Dict) -> str:
    if not isinstance(data, dict):
        return "No response."
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return "No response."
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    if isinstance(content, str):
        return content.strip() or "No response."
    if isinstance(content, list):
        chunks: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks)
    return "No response."


def get_llm_adapter() -> LLMAdapter:
    provider = str(_active_runtime_config()["provider"])
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleAdapter()
    return StubLLMAdapter()
