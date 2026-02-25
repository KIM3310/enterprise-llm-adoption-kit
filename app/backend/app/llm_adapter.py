"""LLM provider adapters with runtime configuration and BYOK support.

Supports five provider backends: ``stub`` (offline deterministic),
``openai``, ``openai_compatible``, ``ollama``, and ``bedrock``.  Runtime settings
can be hot-swapped by Admin users without restarting the server.
Per-user OpenAI API keys (BYOK) are held in-memory for the session.
"""

from dataclasses import dataclass
import os
from threading import Lock
from typing import Dict, List, Optional

import requests

from .config import settings


@dataclass
class LLMResult:
    """Container for an LLM generation result with token counts and cost estimate."""

    text: str
    tokens_in: int
    tokens_out: int
    cost: float


RUNTIME_PROVIDER_OPTIONS = {"stub", "openai", "openai_compatible", "ollama", "bedrock"}
BYOK_FALLBACK_MODEL = "gpt-4o-mini"
OLLAMA_FALLBACK_MODEL = "llama3.1:8b"
BEDROCK_FALLBACK_MODEL = "amazon.nova-micro-v1:0"

_runtime_lock = Lock()
_runtime_overrides: Dict[str, Optional[object]] = {
    "provider": None,
    "model": None,
    "temperature": None,
    "max_tokens": None,
    "timeout_sec": None,
    "openai_base_url": None,
    "ollama_base_url": None,
    "openai_org": None,
    "openai_api_key": None,
}
_user_api_keys_lock = Lock()
_user_api_keys: Dict[str, str] = {}


def _estimate_tokens(text: str) -> int:
    """Estimate token count using chars/4 heuristic (closer to BPE reality for English)."""
    return max(1, len(text) // 4)


def _estimate_cost(tokens_in: int, tokens_out: int) -> float:
    cost_in = (tokens_in / 1000.0) * settings.cost_per_1k_input_tokens
    cost_out = (tokens_out / 1000.0) * settings.cost_per_1k_output_tokens
    return round(cost_in + cost_out, 6)


class LLMAdapter:
    """Abstract base class for LLM provider adapters."""

    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        """Generate a response from the LLM. Must be overridden by subclasses."""
        raise NotImplementedError


def _normalize_provider(value: str) -> str:
    provider = str(value or "stub").strip().lower()
    if provider not in RUNTIME_PROVIDER_OPTIONS:
        raise ValueError(f"provider must be one of {sorted(RUNTIME_PROVIDER_OPTIONS)}")
    return provider


def _normalize_runtime_model(provider: str, model: str) -> str:
    raw = str(model or "").strip()
    if provider == "stub":
        return raw or "stub-llm"
    if provider in {"openai", "openai_compatible"}:
        if not raw or raw.startswith("stub"):
            return BYOK_FALLBACK_MODEL
        return raw
    if provider == "ollama":
        if not raw or raw.startswith("stub"):
            return OLLAMA_FALLBACK_MODEL
        return raw
    if provider == "bedrock":
        if not raw or raw.startswith("stub"):
            return BEDROCK_FALLBACK_MODEL
        return raw
    return raw or "stub-llm"


def _active_runtime_config() -> Dict[str, object]:
    with _runtime_lock:
        snapshot = dict(_runtime_overrides)

    provider_raw = snapshot["provider"]
    model_raw = snapshot["model"]
    temperature_raw = snapshot["temperature"]
    max_tokens_raw = snapshot["max_tokens"]
    timeout_raw = snapshot["timeout_sec"]
    base_url_raw = snapshot["openai_base_url"]
    ollama_base_url_raw = snapshot["ollama_base_url"]
    org_raw = snapshot["openai_org"]
    api_key_raw = snapshot["openai_api_key"]

    provider = _normalize_provider(str(provider_raw or settings.llm_provider or "stub"))
    model = _normalize_runtime_model(provider, str(model_raw or settings.llm_model).strip())
    temperature = float(
        settings.llm_temperature if temperature_raw is None else temperature_raw
    )
    max_tokens = int(settings.llm_max_tokens if max_tokens_raw is None else max_tokens_raw)
    timeout_sec = float(settings.llm_timeout_sec if timeout_raw is None else timeout_raw)
    base_url = str(settings.llm_openai_base_url if base_url_raw is None else base_url_raw).strip()
    ollama_base_url = str(
        settings.llm_ollama_base_url if ollama_base_url_raw is None else ollama_base_url_raw
    ).strip()
    org = str(settings.llm_openai_org if org_raw is None else org_raw).strip()
    api_key = str(settings.llm_openai_api_key if api_key_raw is None else api_key_raw).strip()

    return {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout_sec": timeout_sec,
        "openai_base_url": base_url,
        "ollama_base_url": ollama_base_url,
        "openai_org": org,
        "openai_api_key": api_key,
    }


def _runtime_config_for_request(*, api_key_override: Optional[str] = None) -> Dict[str, object]:
    runtime = _active_runtime_config()
    if api_key_override is not None:
        override_key = str(api_key_override).strip()
        runtime["openai_api_key"] = override_key
        if override_key and str(runtime.get("provider", "stub")) == "stub":
            runtime["provider"] = "openai"
            model = str(runtime.get("model", "")).strip()
            if not model or model.startswith("stub"):
                runtime["model"] = BYOK_FALLBACK_MODEL
    return runtime


def get_llm_runtime_settings() -> Dict[str, object]:
    """Return the current LLM runtime settings with the API key masked."""
    config = _active_runtime_config()
    api_key = str(config.pop("openai_api_key", "")).strip()
    config["openai_api_key_configured"] = bool(api_key)
    return config


def get_llm_runtime_settings_for_request(*, api_key_override: Optional[str] = None) -> Dict[str, object]:
    """Return runtime settings for a specific request, applying any BYOK override."""
    config = _runtime_config_for_request(api_key_override=api_key_override)
    api_key = str(config.pop("openai_api_key", "")).strip()
    config["openai_api_key_configured"] = bool(api_key)
    return config


def set_user_openai_api_key(user_id: str, api_key: str) -> bool:
    """Store a per-user OpenAI API key in memory for BYOK sessions."""
    safe_user_id = str(user_id or "").strip()
    safe_api_key = str(api_key or "").strip()
    if not safe_user_id:
        raise ValueError("user_id is required")
    if not safe_api_key:
        raise ValueError("openai_api_key cannot be empty")
    with _user_api_keys_lock:
        _user_api_keys[safe_user_id] = safe_api_key
    return True


def get_user_openai_api_key(user_id: str) -> str:
    """Retrieve the stored OpenAI API key for *user_id*, or empty string if unset."""
    safe_user_id = str(user_id or "").strip()
    if not safe_user_id:
        return ""
    with _user_api_keys_lock:
        return str(_user_api_keys.get(safe_user_id, "")).strip()


def clear_user_openai_api_key(user_id: str) -> bool:
    """Remove the stored API key for *user_id*. Returns ``True`` if a key was removed."""
    safe_user_id = str(user_id or "").strip()
    if not safe_user_id:
        return False
    with _user_api_keys_lock:
        return _user_api_keys.pop(safe_user_id, None) is not None


def reset_llm_runtime_settings() -> Dict[str, object]:
    """Reset all runtime overrides back to environment-variable defaults."""
    with _runtime_lock:
        for key in _runtime_overrides:
            _runtime_overrides[key] = None
    return get_llm_runtime_settings()


def update_llm_runtime_settings(  # noqa: PLR0913
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout_sec: Optional[float] = None,
    openai_base_url: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    openai_org: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    reset_to_env: bool = False,
) -> Dict[str, object]:
    """Hot-swap LLM runtime settings without restarting the server."""
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
        if ollama_base_url is not None:
            _runtime_overrides["ollama_base_url"] = str(ollama_base_url).strip()
        if openai_org is not None:
            _runtime_overrides["openai_org"] = str(openai_org).strip()
        if openai_api_key is not None:
            _runtime_overrides["openai_api_key"] = str(openai_api_key).strip()

    return get_llm_runtime_settings()


class OpenAICompatibleAdapter(LLMAdapter):
    """Adapter for OpenAI and OpenAI-compatible API endpoints."""
    def __init__(self, runtime: Optional[Dict[str, object]] = None) -> None:
        runtime = runtime or _active_runtime_config()
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


class OllamaAdapter(LLMAdapter):
    """Adapter for locally-hosted Ollama models."""
    def __init__(self, runtime: Optional[Dict[str, object]] = None) -> None:
        runtime = runtime or _active_runtime_config()
        self.base_url = str(runtime["ollama_base_url"]).rstrip("/")
        self.timeout_sec = max(1.0, float(runtime["timeout_sec"]))
        self.model = str(runtime["model"])
        self.temperature = float(runtime["temperature"])
        self.max_tokens = int(runtime["max_tokens"])

    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("Ollama response is not valid JSON") from exc

        text = _extract_ollama_response_text(data)
        tokens_in = int(
            (
                data.get("prompt_eval_count", 0)
                if isinstance(data, dict)
                else 0
            )
            or _estimate_tokens(" ".join([m["content"] for m in messages]))
        )
        tokens_out = int(
            (
                data.get("eval_count", 0)
                if isinstance(data, dict)
                else 0
            )
            or _estimate_tokens(text)
        )
        cost = _estimate_cost(tokens_in, tokens_out)
        return LLMResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)


class BedrockAdapter(LLMAdapter):
    """Adapter for Amazon Bedrock Converse API."""

    def __init__(self, runtime: Optional[Dict[str, object]] = None) -> None:
        runtime = runtime or _active_runtime_config()
        self.region = (
            str(os.getenv("LLM_BEDROCK_REGION", "")).strip()
            or str(os.getenv("AWS_REGION", "")).strip()
            or str(os.getenv("AWS_DEFAULT_REGION", "")).strip()
            or "us-east-1"
        )
        self.timeout_sec = max(1.0, float(runtime["timeout_sec"]))
        self.model = str(runtime["model"])
        self.temperature = float(runtime["temperature"])
        self.max_tokens = int(runtime["max_tokens"])

    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - dependency path
            raise RuntimeError("boto3 is required for Bedrock runtime support") from exc

        client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            config=None,
        )
        conversation = []
        system_prompts = []
        for message in messages:
            role = str(message.get("role", "")).strip().lower()
            content = str(message.get("content", "")).strip()
            if not content:
                continue
            if role == "system":
                system_prompts.append({"text": content})
                continue
            if role not in {"user", "assistant"}:
                role = "user"
            conversation.append({"role": role, "content": [{"text": content}]})

        if not conversation:
            conversation = [{"role": "user", "content": [{"text": f"Summarize signals for {use_case}."}]}]

        request_kwargs = {
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
            "messages": conversation,
            "modelId": self.model,
        }
        if system_prompts:
            request_kwargs["system"] = system_prompts

        try:
            response = client.converse(**request_kwargs)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Bedrock request failed: {exc}") from exc

        output_message = response.get("output", {}).get("message", {})
        content_blocks = output_message.get("content", []) if isinstance(output_message, dict) else []
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict):
                value = block.get("text")
                if isinstance(value, str) and value.strip():
                    text_parts.append(value.strip())
        text = "\n".join(text_parts).strip() or "No response."

        usage = response.get("usage", {}) if isinstance(response, dict) else {}
        tokens_in = int(usage.get("inputTokens") or _estimate_tokens(" ".join([m["content"] for m in messages])))
        tokens_out = int(usage.get("outputTokens") or _estimate_tokens(text))
        cost = _estimate_cost(tokens_in, tokens_out)
        return LLMResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)


class StubLLMAdapter(LLMAdapter):
    """Offline deterministic adapter for testing and demo mode."""
    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        # Offline-first deterministic "good enough" responses.
        user_text = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        context_text = next(
            (
                m.get("content", "")
                for m in reversed(messages)
                if m.get("role") == "assistant" and "CONTEXT:" in str(m.get("content", ""))
            ),
            "",
        )

        def extract_citations(text: str) -> List[str]:
            # Context lines are formatted like: "[DOC_ID:field_path] content..."
            # `field_path` can include bracket characters (e.g., `runbook_steps[0]`), so avoid regexes
            # that treat `]` as a terminator. Instead, parse the first marker per line.
            items: List[str] = []
            for raw_line in str(text or "").splitlines():
                line = raw_line.strip()
                if not line.startswith("[") or ":" not in line:
                    continue
                start = 1
                colon = line.find(":", start)
                if colon == -1:
                    continue
                # Prefer the marker terminator `] ` (end bracket followed by a space),
                # otherwise fall back to the last `]` in the line.
                end = line.find("] ", colon + 1)
                if end == -1:
                    end = line.rfind("]")
                if end == -1 or end <= colon:
                    continue
                doc_id = line[start:colon].strip()
                field = line[colon + 1:end].strip()
                if doc_id and field:
                    items.append(f"{doc_id}::{field}")
            seen = set()
            unique = []
            for item in items:
                if item in seen:
                    continue
                seen.add(item)
                unique.append(item)
            return unique[:6]

        def pick_keywords(text: str) -> List[str]:
            lower = str(text or "").lower()
            candidates = [
                "rbac",
                "audit",
                "pii",
                "injection",
                "egress",
                "kms",
                "breakglass",
                "timeout",
                "retry",
                "circuit",
                "drift",
                "latency",
                "cost",
            ]
            return [c for c in candidates if c in lower][:6]

        citations = extract_citations(context_text)
        keywords = pick_keywords(f"{user_text}\n{context_text}")

        if use_case == "uc1":
            lines = []
            lines.append("Adoption risk review (offline stub mode).")
            lines.append("")
            lines.append("Top risks:")
            # Keep the list stable but slightly contextual.
            if any(k in keywords for k in ["rbac", "audit", "pii"]):
                lines.append("- Data access leakage if retrieval is not strictly role-filtered (RBAC at retrieval + post-check).")
                lines.append("- Audit/PII handling risk if raw prompts/responses are persisted without hashing/redaction.")
            if any(k in keywords for k in ["injection"]):
                lines.append("- Prompt injection can bypass intended tool/use-case boundaries without explicit safety policies.")
            if any(k in keywords for k in ["egress", "kms", "breakglass"]):
                lines.append("- Privileged egress and key-management paths need breakglass controls and change auditing.")
            if any(k in keywords for k in ["timeout", "retry", "circuit", "latency"]):
                lines.append("- Reliability risk: upstream timeouts can cascade without timeouts/retries/circuit breakers.")
            if any(k in keywords for k in ["drift"]):
                lines.append("- Quality risk: retrieval/answer quality drifts as documents and query patterns evolve.")
            if "cost" in keywords:
                lines.append("- Budget risk: uncontrolled context size and retries can inflate token spend.")
            if len(lines) == 3:
                lines.append("- Validate least-privilege, grounding, and operational readiness before rollout.")

            lines.append("")
            lines.append("Recommended next actions:")
            lines.append("- Run the Scenario Runner and export a validation report for operators.")
            lines.append("- Verify citations are relevant and stable across roles (Employee vs Ops/Admin).")
            lines.append("- Set explicit cost/latency guardrails and monitor via /metrics.")
            if citations:
                lines.append("")
                lines.append("Context references (parsed):")
                for item in citations:
                    lines.append(f"- {item}")
            response = "\n".join(lines)
        else:
            # UC2 log intelligence
            logs_preview = str(context_text or "")
            # Try to extract the first line after "LOGS:" if present.
            extracted_logs = ""
            if "LOGS:" in logs_preview:
                after = logs_preview.split("LOGS:", 1)[1]
                extracted_logs = after.strip().splitlines()[0:3]
                extracted_logs = "\n".join(extracted_logs).strip()
            if not extracted_logs:
                extracted_logs = str(user_text or "").strip()

            lines = []
            lines.append("Incident log summary (offline stub mode).")
            if extracted_logs:
                lines.append("")
                lines.append("Observed signal:")
                lines.append("```")
                lines.append(extracted_logs[:500])
                lines.append("```")
            lines.append("")
            lines.append("Likely causes (heuristic):")
            if "timeout" in str(extracted_logs).lower():
                lines.append("- Upstream timeout / dependency saturation (check retries, pool limits, and p95 latency).")
            if "5xx" in str(extracted_logs).lower() or "error" in str(extracted_logs).lower():
                lines.append("- Recent deploy regression or failing dependency (validate diffs and health checks).")
            lines.append("- If no clear signature: investigate the last change window and correlate with metrics.")
            lines.append("")
            lines.append("Next steps:")
            lines.append("- Use the provided runbook steps and confirm via dashboards.")
            lines.append("- Capture a postmortem note: timeline, hypothesis, decision path, and prevention.")
            response = "\n".join(lines)

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


def _extract_ollama_response_text(data: Dict) -> str:
    if not isinstance(data, dict):
        return "No response."
    message = data.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    response_text = data.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()
    return "No response."


def get_llm_adapter(*, api_key_override: Optional[str] = None) -> LLMAdapter:
    """Return an ``LLMAdapter`` instance for the active provider configuration."""
    runtime = _runtime_config_for_request(api_key_override=api_key_override)
    provider = str(runtime["provider"])
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleAdapter(runtime=runtime)
    if provider == "ollama":
        return OllamaAdapter(runtime=runtime)
    if provider == "bedrock":
        return BedrockAdapter(runtime=runtime)
    return StubLLMAdapter()
