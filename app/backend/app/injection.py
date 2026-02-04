from typing import List, Tuple

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard above",
    "system prompt",
    "developer message",
    "you are now",
    "reveal your rules",
    "tool override",
    "bypass policy",
]


def detect_injection(text: str) -> Tuple[bool, List[str]]:
    lowered = text.lower()
    hits = [p for p in INJECTION_PATTERNS if p in lowered]
    return (len(hits) > 0), hits

