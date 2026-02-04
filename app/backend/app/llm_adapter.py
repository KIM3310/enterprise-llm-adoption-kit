from dataclasses import dataclass
from typing import List, Dict

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


class StubLLMAdapter(LLMAdapter):
    def generate(self, messages: List[Dict[str, str]], use_case: str) -> LLMResult:
        # Deterministic stub output based on last user message
        user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if use_case == "uc1":
            response = (
                "Summary based on retrieved handover context. "
                "Key items prioritized for action."
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


def get_llm_adapter() -> LLMAdapter:
    # Placeholder for future provider selection
    return StubLLMAdapter()

