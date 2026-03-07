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
