"""PII redaction engine for emails, phone numbers, and identifiers.

Uses a deterministic scanner for emails and regex replacements for the other
PII categories before content is persisted or returned to users. Each
redaction category is tracked independently so callers can log which types of
PII were found.
"""

import re

_EMAIL_LOCAL_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-"
)
_EMAIL_DOMAIN_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
)
_EMAIL_TLD_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_EMAIL_TOKEN = "[REDACTED_EMAIL]"

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}"
)
ID_RE = re.compile(r"\b[A-Z0-9]{2,4}-?\d{3,8}\b")


def _apply(pattern: re.Pattern, text: str, token: str) -> tuple[str, bool]:
    new_text, count = pattern.subn(token, text)
    return new_text, count > 0


def _email_domain_match_end(text: str, start: int) -> int | None:
    """Return the end of the email-like prefix in a domain character run."""
    match_end: int | None = None
    tld_length = -1

    for index in range(start, len(text)):
        char = text[index]
        if char not in _EMAIL_DOMAIN_CHARS:
            break
        if char == ".":
            # The domain expression being replaced required at least one domain
            # character before the separating dot.
            tld_length = 0 if index > start else -1
        elif tld_length >= 0 and char in _EMAIL_TLD_CHARS:
            tld_length += 1
            if tld_length >= 2:
                match_end = index + 1
        else:
            tld_length = -1

    return match_end


def _redact_emails(text: str) -> tuple[str, bool]:
    """Redact email-like tokens with a deterministic linear-time scan.

    The accepted ASCII character sets mirror the previous email matcher. The
    scan moves over maximal local-part and domain runs rather than retrying a
    pattern at every input position. Each character is therefore inspected a
    constant number of times, including when a malformed candidate is followed
    by another ``@``.
    """
    chunks: list[str] = []
    cursor = 0
    index = 0
    text_length = len(text)

    while index < text_length:
        if text[index] not in _EMAIL_LOCAL_CHARS:
            index += 1
            continue

        # A candidate must begin at the start of a local-part run. This check is
        # relevant when a valid match ends before the surrounding run does.
        if index > 0 and text[index - 1] in _EMAIL_LOCAL_CHARS:
            index += 1
            continue

        local_start = index
        while index < text_length and text[index] in _EMAIL_LOCAL_CHARS:
            index += 1

        if index >= text_length or text[index] != "@":
            continue

        domain_start = index + 1
        match_end = _email_domain_match_end(text, domain_start)
        if match_end is None:
            # The character after ``@`` is a new possible local-part boundary.
            index += 1
            continue

        chunks.append(text[cursor:local_start])
        chunks.append(_EMAIL_TOKEN)
        cursor = match_end
        index = match_end

    if not chunks:
        return text, False

    chunks.append(text[cursor:])
    return "".join(chunks), True


def redact_text(text: str) -> tuple[str, dict[str, bool]]:
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
    redacted, hit = _redact_emails(text)
    events["email"] = hit
    redacted, hit = _apply(PHONE_RE, redacted, "[REDACTED_PHONE]")
    events["phone"] = hit
    redacted, hit = _apply(ID_RE, redacted, "[REDACTED_ID]")
    events["id"] = hit
    return redacted, events
