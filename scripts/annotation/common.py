"""Common constants, data schemas, and helper functions for AI-assisted annotation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

# ==============================================================================
# Repository Directory Paths
# ==============================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_ANNOTATOR_FILE = REPO_ROOT / "track_a_annotation" / "annotator_a" / "TRACK_A_ANNOTATOR_A.jsonl"
DEFAULT_AI_DIR = REPO_ROOT / "track_a_annotation" / "ai_assisted"
DEFAULT_RECOMMENDATIONS_FILE = DEFAULT_AI_DIR / "AI_RECOMMENDATIONS_V1.jsonl"
DEFAULT_DECISIONS_FILE = DEFAULT_AI_DIR / "RESEARCHER_DECISIONS_V1.jsonl"
DEFAULT_REVIEW_REPORT_FILE = DEFAULT_AI_DIR / "REVIEW_REPORT_V1.md"
DEFAULT_SESSION_CONFIG_FILE = DEFAULT_AI_DIR / "SESSION_CONFIG_V1.json"
DEFAULT_COMMIT_AUDIT_REPORT = DEFAULT_AI_DIR / "COMMIT_AUDIT_REPORT_V1.md"
DEFAULT_COMMIT_AUDIT_JSON = DEFAULT_AI_DIR / "COMMIT_AUDIT_REPORT_V1.json"
DEFAULT_COMMITTED_ANNOTATOR_FILE = DEFAULT_AI_DIR / "TRACK_A_ANNOTATOR_A_COMMITTED.jsonl"

DEFAULT_SCHEMA_FILE = REPO_ROOT / "TRACK_A_ANNOTATION_SCHEMA_V2.json"
DEFAULT_SYSTEM_PROMPT_FILE = (
    REPO_ROOT / "track_a_annotation" / "decision_batches" / "TRACK_A_LLM_SYSTEM_PROMPT_V2.txt"
)
DEFAULT_ADJUDICATION_PROMPT_FILE = (
    REPO_ROOT / "track_a_annotation" / "decision_batches" / "TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt"
)
DEFAULT_CHALLENGE_PROMPT_FILE = (
    REPO_ROOT / "track_a_annotation" / "decision_batches" / "TRACK_A_LLM_CHALLENGE_PROMPT_V2.txt"
)
DEFAULT_ADJUDICATION_SCHEMA_FILE = (
    REPO_ROOT / "track_a_annotation" / "decision_batches" / "TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json"
)

# ==============================================================================
# Canonical Label and Grade Mappings (Schema V2)
# ==============================================================================
LABEL_TO_GRADE: dict[str, int | None] = {
    "RELEVANT": 2,
    "PARTIALLY_RELEVANT": 1,
    "IRRELEVANT": 0,
    "INSUFFICIENT_INFORMATION": 0,
    "AMBIGUOUS": None,
}

VALID_LABELS = set(LABEL_TO_GRADE.keys())

VALID_STATES = {
    "UNANNOTATED",
    "IN_PROGRESS",
    "ANNOTATED",
    "QA_FLAGGED",
    "QA_RESOLVED",
    "FROZEN",
}

VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}

# Provenance identifiers
PROVENANCE_AI_RECOMMENDATION = "AI_RECOMMENDATION"
PROVENANCE_AI_ASSISTED_CONFIRMED = "AI_ASSISTED_HUMAN_CONFIRMED"
PROVENANCE_AI_ASSISTED_OVERRIDDEN = "AI_ASSISTED_HUMAN_OVERRIDDEN"
PROVENANCE_DEFERRED = "DEFERRED_PENDING_ADJUDICATION"
PROVENANCE_REJECTED = "AI_RECOMMENDATION_REJECTED"
PROVENANCE_HUMAN = "HUMAN"

# ==============================================================================
# Provider Specifications & Default Endpoints
# ==============================================================================
PROVIDER_CONFIGS: dict[str, dict[str, Any]] = {
    "groq": {
        "default_model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "GROQ_API_KEY",
        "fallback_env_keys": [],
    },
    "nvidia": {
        "default_model": "meta/llama-3.3-70b-instruct",
        "base_url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "env_key": "NVIDIA_LLM_API_KEY",
        "fallback_env_keys": ["NVIDIA_API_KEY"],
    },
    "gemini": {
        "default_model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "env_key": "GEMINI_API_KEY",
        "fallback_env_keys": ["GOOGLE_API_KEY"],
    },
    "cloudflare": {
        "default_model": "@cf/meta/llama-3.3-70b-instruct",
        "base_url_template": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions",
        "env_key": "CLOUDFLARE_API_KEY",
        "fallback_env_keys": [],
        "account_env_key": "CLOUDFLARE_ACCOUNT_ID",
    },
    "openai": {
        "default_model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "env_key": "OPENAI_API_KEY",
        "fallback_env_keys": [],
    },
    "openai_compatible": {
        "default_model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "OPENAI_API_KEY",
        "fallback_env_keys": ["GROQ_API_KEY", "NVIDIA_LLM_API_KEY"],
    },
}


# ==============================================================================
# Hash and Text Utilities
# ==============================================================================
def compute_sha256(text: str | bytes) -> str:
    """Compute deterministic SHA-256 hex digest for given text or bytes."""
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 checksum of an entire file."""
    path = Path(file_path)
    if not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


# ==============================================================================
# Prompt and Schema Loaders
# ==============================================================================
def load_file_text_safe(path: Path | str, fallback: str = "") -> str:
    """Safely load text file with UTF-8 encoding."""
    p = Path(path)
    if p.is_file():
        return p.read_text(encoding="utf-8").strip()
    return fallback


def load_prompts_and_hashes(
    system_prompt_path: Path | str = DEFAULT_SYSTEM_PROMPT_FILE,
    adjudication_prompt_path: Path | str = DEFAULT_ADJUDICATION_PROMPT_FILE,
    challenge_prompt_path: Path | str = DEFAULT_CHALLENGE_PROMPT_FILE,
    adjudication_schema_path: Path | str = DEFAULT_ADJUDICATION_SCHEMA_FILE,
) -> dict[str, Any]:
    """Load prompt templates, schema, and compute their SHA-256 hashes."""
    fallback_sys = "You are an evidence-based semantic medical adjudicator."
    fallback_adj = (
        "You are a strict medical semantic adjudicator. Determine if the supplied "
        "evidence materially addresses the research query.\n\n"
        "Query: {query}\nEvidence:\n{evidence}\n"
    )
    fallback_chal = "Attempt to overturn the proposed semantic annotation."

    sys_text = load_file_text_safe(system_prompt_path, fallback_sys)
    adj_text = load_file_text_safe(adjudication_prompt_path, fallback_adj)
    chal_text = load_file_text_safe(challenge_prompt_path, fallback_chal)

    schema_obj: dict[str, Any] = {}
    schema_path_p = Path(adjudication_schema_path)
    if schema_path_p.is_file():
        try:
            schema_obj = json.loads(schema_path_p.read_text(encoding="utf-8"))
        except Exception:
            schema_obj = {}

    schema_str = json.dumps(schema_obj, sort_keys=True, separators=(",", ":"))

    return {
        "system_prompt": sys_text,
        "adjudication_prompt_template": adj_text,
        "challenge_prompt": chal_text,
        "adjudication_schema": schema_obj,
        "hashes": {
            "system_prompt_sha256": compute_sha256(sys_text),
            "adjudication_prompt_sha256": compute_sha256(adj_text),
            "challenge_prompt_sha256": compute_sha256(chal_text),
            "adjudication_schema_sha256": compute_sha256(schema_str),
        },
    }


# ==============================================================================
# JSONL Read/Write Operations
# ==============================================================================
def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """Load records from a JSONL file, ignoring empty lines."""
    p = Path(path)
    if not p.is_file():
        return []
    records = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records


def save_jsonl(path: Path | str, records: list[dict[str, Any]], mode: str = "w") -> None:
    """Save records to a JSONL file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open(mode, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def append_jsonl(path: Path | str, record: dict[str, Any]) -> None:
    """Append a single record to a JSONL file with flush."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


# ==============================================================================
# Validation Helpers
# ==============================================================================
def normalize_label(label: str | None) -> str | None:
    """Normalize label string to standard uppercase canonical enum."""
    if not label:
        return None
    cleaned = str(label).strip().upper().replace(" ", "_").replace("-", "_")
    if cleaned in VALID_LABELS:
        return cleaned
    # Common synonyms/abbreviations
    synonyms = {
        "DIRECT_SUPPORT": "RELEVANT",
        "PARTIAL_SUPPORT": "PARTIALLY_RELEVANT",
        "NOT_RELEVANT": "IRRELEVANT",
        "INSUFFICIENT": "INSUFFICIENT_INFORMATION",
        "AMBIGUOUS": "AMBIGUOUS",
    }
    return synonyms.get(cleaned, cleaned)


def verify_span_substring(span: str | None, evidence: str | None) -> tuple[bool, str]:
    """Verify that evidence_span is an exact contiguous substring of evidence.

    Returns:
        (is_valid, matched_span_or_reason)
    """
    if span is None or span == "":
        return True, ""
    if evidence is None or evidence == "":
        return False, "Evidence text is empty but span was provided."

    span_clean = span.strip()
    if not span_clean:
        return True, ""

    # Exact check
    if span_clean in evidence:
        return True, span_clean

    # Strip surrounding quotation marks if present
    stripped_quotes = span_clean.strip("\"'«»“”")
    if stripped_quotes and stripped_quotes in evidence:
        return True, stripped_quotes

    # Case-insensitive search fallback check
    ev_lower = evidence.lower()
    span_lower = span_clean.lower()
    pos = ev_lower.find(span_lower)
    if pos != -1:
        # Found exact substring case-insensitively, extract original slice
        exact_match = evidence[pos : pos + len(span_clean)]
        return True, exact_match

    return False, f"Span not found in retrieved evidence: '{span_clean[:50]}...'"


def extract_json_from_llm(raw_text: str) -> dict[str, Any]:
    """Extract valid JSON from LLM output, handling markdown code fences."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[len("```json") :].strip()
    elif text.startswith("```"):
        text = text[len("```") :].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    # Attempt 1: direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Attempt 2: find first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    raise ValueError(f"Could not parse valid JSON object from LLM response:\n{raw_text[:300]}")
