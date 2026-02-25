"""Prompt-injection detection using keyword heuristics.

Scans user input for known prompt-injection phrases and returns both a
boolean flag and the list of matched patterns so callers can log the
specific triggers.
"""

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
    """Check *text* for known prompt-injection patterns.

    Args:
        text: The raw user input to scan.

    Returns:
        A tuple of ``(detected, matched_patterns)`` where *detected* is
        ``True`` when at least one pattern matched.
    """
    lowered = text.lower()
    hits = [p for p in INJECTION_PATTERNS if p in lowered]
    return (len(hits) > 0), hits

