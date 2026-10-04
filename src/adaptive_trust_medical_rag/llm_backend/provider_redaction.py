"""Deterministic secret redaction for log and error output.

Scrubs provider API keys, bearer tokens, and authorization headers
from text before it is written to logs, invocation ledgers, error
messages, or diagnostic output. Adapted from log-redaction patterns
in FreeLLMAPI (MIT, tashfeenahmed/freellmapi), translated to Python.

Architecture:
    RAW SECURE ARTIFACT   → never redacted, restricted access
    SAFE LOG OUTPUT        → always redacted via redact_secrets()

This module is applied at LOG-WRITE BOUNDARIES only. It does NOT:
- modify evidence text before scientific analysis
- alter RAG pipeline content
- change trust scores or security gate input
- monkey-patch stdout/stderr globally

Integration point:
    record_invocation(error_message=redact_secrets(str(e)[:200]))
    record_failure(error=redact_secrets(str(e)))
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REDACTED = "[REDACTED]"
REDACTED_BEARER = "Bearer [REDACTED]"


# ── Key-format patterns ───────────────────────────────────────────────
# Ordered most-specific first. Each pattern targets a known provider
# key format. Patterns are intentionally conservative: they require a
# word boundary (\b) and a minimum length to avoid false positives on
# normal text like SHA-256 hashes, case IDs, or medical terms.

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Groq keys: gsk_ followed by 8+ alphanum chars
    (re.compile(r"\bgsk_[A-Za-z0-9_\-]{8,}"), REDACTED),
    # OpenAI-style keys: sk- followed by 8+ alphanum chars
    # (also OpenRouter, SiliconFlow, etc.)
    (re.compile(r"\bsk-[A-Za-z0-9_\-/+=]{8,}"), REDACTED),
    # Google API keys: AIza followed by 20+ chars
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}"), REDACTED),
    # NVIDIA keys: nvapi- prefix
    (re.compile(r"\bnvapi-[A-Za-z0-9_\-]{8,}"), REDACTED),
    # HuggingFace tokens: hf_ prefix
    (re.compile(r"\bhf_[A-Za-z0-9]{16,}"), REDACTED),
    # Cerebras keys: csk- prefix
    (re.compile(r"\bcsk-[A-Za-z0-9_\-]{8,}"), REDACTED),

    # Bearer tokens in text or headers (generic catch-all for auth)
    # Negative lookahead prevents double-redacting already-redacted text
    (re.compile(
        r"Bearer\s+(?!\[REDACTED\])[A-Za-z0-9._~+/\-]+=*",
        re.IGNORECASE,
    ), REDACTED_BEARER),

    # Authorization header values in JSON/dict-like output
    (re.compile(
        r'(["\']?(?:authorization|x-api-key|x-goog-api-key)["\']?\s*[:=]\s*["\']?)'
        r'(?!\[REDACTED\])[^"\',\s}\]&]+',
        re.IGNORECASE,
    ), rf"\1{REDACTED}"),
]


@dataclass(frozen=True)
class RedactionResult:
    """Result of a redaction operation.

    Attributes:
        text: The redacted output text (safe for logging).
        redaction_count: Number of secrets replaced.
    """

    text: str
    redaction_count: int


def redact_secrets(text: str) -> str:
    """Remove credentials from text, preserving all other content.

    This is the primary public API. Returns the redacted string only.
    Use redact_secrets_detailed() to also get a count of replacements.

    Args:
        text: Input text that may contain credentials.

    Returns:
        Text with all detected credentials replaced by [REDACTED].
    """
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_secrets_detailed(text: str) -> RedactionResult:
    """Remove credentials and report how many were found.

    Args:
        text: Input text that may contain credentials.

    Returns:
        RedactionResult with redacted text and count of replacements.
    """
    total_count = 0
    for pattern, replacement in _PATTERNS:
        text, count = pattern.subn(replacement, text)
        total_count += count
    return RedactionResult(text=text, redaction_count=total_count)
