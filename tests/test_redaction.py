import pytest
from app.redaction import redact_text

EMAIL_TOKEN = "[REDACTED_EMAIL]"


def test_redaction_email_phone_id():
    text = "Contact me at test@example.com or 010-1234-5678 id AB-12345"
    redacted, events = redact_text(text)
    assert EMAIL_TOKEN in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_ID]" in redacted
    assert events["email"]
    assert events["phone"]
    assert events["id"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Email first.last+alerts%team@sub-domain.example.co.uk.",
            f"Email {EMAIL_TOKEN}.",
        ),
        (
            "Primary a_b@example.com; backup ops+night@sub.example.io!",
            f"Primary {EMAIL_TOKEN}; backup {EMAIL_TOKEN}!",
        ),
        (
            "Recover from malformed prefix: bad@user@example.com",
            f"Recover from malformed prefix: bad@{EMAIL_TOKEN}",
        ),
    ],
)
def test_redaction_handles_email_edge_cases(text, expected):
    redacted, events = redact_text(text)

    assert redacted == expected
    assert events == {"email": True, "phone": False, "id": False}


@pytest.mark.parametrize(
    "text",
    [
        "One-letter TLD user@example.c is not enough",
        "A domain separator is required for user@example",
        "A local part is required for @example.com",
    ],
)
def test_redaction_leaves_non_email_candidates_unchanged(text):
    redacted, events = redact_text(text)

    assert redacted == text
    assert not any(events.values())


@pytest.mark.parametrize(
    "text",
    [
        "%" * 16_384,
        "a@" + ("a" * 16_384),
        "a@" + ("a." * 4_096) + "x",
    ],
)
def test_email_scanner_handles_bounded_malformed_inputs(text):
    redacted, events = redact_text(text)

    assert redacted == text
    assert not any(events.values())


def test_email_scanner_recovers_after_bounded_at_sign_chain():
    malformed_prefix = "a@" * 4_096
    text = malformed_prefix + "safe@example.com"

    redacted, events = redact_text(text)

    assert redacted == malformed_prefix + EMAIL_TOKEN
    assert events == {"email": True, "phone": False, "id": False}
