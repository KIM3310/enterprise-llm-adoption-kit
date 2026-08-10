"""PII redaction engine for emails, phone numbers, and identifiers.

Applies regex-based replacements to mask personally identifiable
information before content is persisted or returned to users.  Each
redaction category is tracked independently so callers can log which
types of PII were found.
"""

import re
from typing import Dict, Tuple

# Require the start of a local-part run. Without this boundary, a failed match on
# a long run such as ``%%%%...`` is retried at every character, producing
# quadratic backtracking on attacker-controlled request bodies.
EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}"
)
ID_RE = re.compile(r"\b[A-Z0-9]{2,4}-?\d{3,8}\b")


def _apply(pattern: re.Pattern, text: str, token: str) -> Tuple[str, bool]:
    new_text, count = pattern.subn(token, text)
    return new_text, count > 0


def redact_text(text: str) -> Tuple[str, Dict[str, bool]]:
    """Replace PII tokens in *text* with ``[REDACTED_*]`` placeholders.

    Args:
        text: The input string to scan and redact.

    Returns:
        A tuple of ``(redacted_text, event_flags)`` where *event_flags*
        maps each category (``email``, ``phone``, ``id``) to whether a
        match was found.
    """
    events = {
        "email": False,
        "phone": False,
        "id": False,
    }
    redacted, hit = _apply(EMAIL_RE, text, "[REDACTED_EMAIL]")
    events["email"] = hit
    redacted, hit = _apply(PHONE_RE, redacted, "[REDACTED_PHONE]")
    events["phone"] = hit
    redacted, hit = _apply(ID_RE, redacted, "[REDACTED_ID]")
    events["id"] = hit
    return redacted, events

