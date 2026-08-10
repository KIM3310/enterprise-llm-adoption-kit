import time

from app.redaction import redact_text


def test_redaction_email_phone_id():
    text = "Contact me at test@example.com or 010-1234-5678 id AB-12345"
    redacted, events = redact_text(text)
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_ID]" in redacted
    assert events["email"]
    assert events["phone"]
    assert events["id"]


def test_redaction_handles_adversarial_percent_run_in_linear_time():
    text = "%" * 64_000

    started = time.perf_counter()
    redacted, events = redact_text(text)
    elapsed = time.perf_counter() - started

    assert redacted == text
    assert not any(events.values())
    # The vulnerable expression takes several seconds at this size, while the
    # boundary-anchored expression completes in a few milliseconds.
    assert elapsed < 0.5
