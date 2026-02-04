import re
from typing import Dict, Tuple

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}"
)
ID_RE = re.compile(r"\b[A-Z0-9]{2,4}-?\d{3,8}\b")


def _apply(pattern: re.Pattern, text: str, token: str) -> Tuple[str, bool]:
    new_text, count = pattern.subn(token, text)
    return new_text, count > 0


def redact_text(text: str) -> Tuple[str, Dict[str, bool]]:
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

