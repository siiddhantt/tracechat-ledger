import re

MAX_PREVIEW_CHARS = 500

PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[email]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[card]"),
    (re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d\b"), "[phone]"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b"), "[secret]"),
)


def redact_text(value: str) -> str:
    redacted = value
    for pattern, replacement in PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def preview(value: str | None, *, limit: int = MAX_PREVIEW_CHARS) -> str | None:
    if value is None:
        return None
    compact = " ".join(redact_text(value).split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: max(0, limit - 3)]}..."


def title_from_message(value: str) -> str:
    compact = preview(value, limit=60) or "Untitled chat"
    return compact if compact else "Untitled chat"
