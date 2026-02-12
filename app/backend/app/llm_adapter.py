from dataclasses import dataclass
from typing import List, Dict

import requests

from .config import settings


@dataclass
class LLMResult:
    text: str
    tokens_in: int
    tokens_out: int
    cost: float


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _estimate_cost(tokens_in: int, tokens_out: int) -> float:
    cost_in = (tokens_in / 1000.0) * settings.cost_per_1k_input_tokens
    cost_out = (tokens_out / 1000.0) * settings.cost_per_1k_output_tokens
    return round(cost_in + cost_out, 6)


class LLMAdapter:
    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        raise NotImplementedError


class OpenAICompatibleAdapter(LLMAdapter):
    def __init__(self) -> None:
        self.base_url = settings.llm_openai_base_url.rstrip("/")
        self.api_key = settings.llm_openai_api_key
        self.organization = settings.llm_openai_org
        self.timeout_sec = max(1.0, settings.llm_timeout_sec)

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
            "model": settings.llm_model,
            "messages": messages,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
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
    provider = (settings.llm_provider or "stub").strip().lower()
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleAdapter()
    return StubLLMAdapter()
