"""Input sanitization and prompt injection defense.

Implements the security rules from security.md:
    - Every incoming user query and retrieved document chunk must undergo
      deterministic regex and semantic sanitization.
    - Prompt injection markers must be escaped or stripped.
    - Injected documents must never alter the LLM system prompt framing.

This module is intentionally dependency-free (stdlib only) so it can run
as the FIRST gate in the pipeline with zero risk of import-order issues.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Injection marker patterns (deterministic regex — no LLM required)
# ─────────────────────────────────────────────────────────────────────────────

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    # Direct override directives
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?(?:a|an|the)\s+", re.IGNORECASE),
    # System-prompt frame markers
    re.compile(r"\bSYSTEM\s*PROMPT\s*:", re.IGNORECASE),
    re.compile(r"\bSYSTEM\s*MESSAGE\s*:", re.IGNORECASE),
    re.compile(r"\bUSER\s*MESSAGE\s*:", re.IGNORECASE),
    re.compile(r"\bASSISTANT\s*:", re.IGNORECASE),
    # Common LLM / chat template tokens
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"<\|system\|>", re.IGNORECASE),
    re.compile(r"<\|user\|>", re.IGNORECASE),
    re.compile(r"<\|assistant\|>", re.IGNORECASE),
    # HTML / script injection
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"</script>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    # Encoded payload markers
    re.compile(r"base64\s*decode", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    # Jailbreak patterns
    re.compile(r"DAN\s*mode", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"do\s+anything\s+now", re.IGNORECASE),
]

# Patterns that should raise a hard REJECT (not just strip)
_HARD_REJECT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:.*", re.IGNORECASE),
]

# ─────────────────────────────────────────────────────────────────────────────
# PHI detection heuristics (fast regex — NOT a replacement for a PHI scanner)
# ─────────────────────────────────────────────────────────────────────────────

_PHI_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("MRN", re.compile(r"\bMRN\s*[:#]?\s*\d{5,10}\b", re.IGNORECASE)),
    ("DOB", re.compile(
        r"\b(?:DOB|Date\s+of\s+Birth)\s*[:#]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        re.IGNORECASE,
    )),
    ("PHONE", re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b")),
    ("NPI", re.compile(r"\bNPI\s*[:#]?\s*\d{10}\b", re.IGNORECASE)),
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


class SanitizationResult:
    """Result of sanitizing a single text input."""

    def __init__(
        self,
        original: str,
        sanitized: str,
        rejected: bool,
        injection_markers_found: list[str],
        phi_patterns_found: list[str],
    ) -> None:
        self.original = original
        self.sanitized = sanitized
        self.rejected = rejected
        self.injection_markers_found = injection_markers_found
        self.phi_patterns_found = phi_patterns_found

    @property
    def is_clean(self) -> bool:
        return (
            not self.rejected
            and not self.injection_markers_found
            and not self.phi_patterns_found
        )


def strip_injection_markers(text: str) -> tuple[str, list[str]]:
    """Strip known prompt injection markers. Returns (cleaned_text, found_markers)."""
    found: list[str] = []
    cleaned = text
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            found.append(pattern.pattern)
            cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned, found


def detect_phi(text: str) -> list[str]:
    """Detect PHI-like patterns. Returns list of pattern names found."""
    found = []
    for name, pattern in _PHI_PATTERNS:
        if pattern.search(text):
            found.append(name)
    return found


def sanitize_query(text: str) -> SanitizationResult:
    """Full sanitization gate for an incoming user query.

    Steps:
        1. Hard-reject check (XSS/script injection).
        2. PHI detection.
        3. Injection marker stripping.

    Returns SanitizationResult. If rejected=True the caller MUST NOT
    pass the text to any downstream component.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    # Step 1: Hard reject
    for pattern in _HARD_REJECT_PATTERNS:
        if pattern.search(text):
            logger.warning("Hard-reject triggered by pattern: %s", pattern.pattern)
            return SanitizationResult(
                original=text,
                sanitized="",
                rejected=True,
                injection_markers_found=[pattern.pattern],
                phi_patterns_found=[],
            )

    # Step 2: PHI detection
    phi_found = detect_phi(text)
    if phi_found:
        logger.warning("PHI pattern(s) detected: %s — input rejected.", phi_found)
        return SanitizationResult(
            original=text,
            sanitized="",
            rejected=True,
            injection_markers_found=[],
            phi_patterns_found=phi_found,
        )

    # Step 3: Injection marker stripping
    cleaned, markers = strip_injection_markers(text)
    if markers:
        logger.warning("Injection markers stripped from input: %s", markers)

    return SanitizationResult(
        original=text,
        sanitized=cleaned,
        rejected=False,
        injection_markers_found=markers,
        phi_patterns_found=[],
    )


def sanitize_document_chunk(text: str) -> SanitizationResult:
    """Sanitize a retrieved document chunk before feeding into LLM context.

    Retrieved documents are treated as untrusted data (AGENTS.md rule 3.1).
    Same pipeline as sanitize_query.
    """
    return sanitize_query(text)
