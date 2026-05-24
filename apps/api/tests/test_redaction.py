from app.utils.redaction import preview, redact_text, title_from_message


def test_redacts_common_pii() -> None:
    value = "Email sid@example.com, phone +1 415-555-0123, card 4242 4242 4242 4242"

    redacted = redact_text(value)

    assert "sid@example.com" not in redacted
    assert "415-555-0123" not in redacted
    assert "4242 4242" not in redacted
    assert "[email]" in redacted
    assert "[phone]" in redacted
    assert "[card]" in redacted


def test_preview_compacts_and_limits() -> None:
    value = "hello\n\n" + "world " * 100

    result = preview(value, limit=20)

    assert result is not None
    assert len(result) == 20
    assert "\n" not in result
    assert result.endswith("...")


def test_title_from_message_uses_safe_fallback() -> None:
    assert title_from_message("   ") == "Untitled chat"
