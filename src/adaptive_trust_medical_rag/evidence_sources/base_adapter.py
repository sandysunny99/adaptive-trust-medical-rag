"""Base Evidence Source Adapter Architecture

Project: Adaptive Trust-Aware Medical RAG
Component: EvidenceSourceAdapter Interface

Defines the abstract contract, canonical serialization, SHA-256 response hashing,
content sanitization, and dual execution modes (LIVE vs FROZEN_SNAPSHOT).
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from adaptive_trust_medical_rag.security.sanitizer import sanitize_query


class AdapterExecutionMode(str, Enum):
    LIVE_API_MODE = "live"
    FROZEN_SNAPSHOT_MODE = "frozen_snapshot"


class EvidenceSourceAdapter(ABC):
    """Abstract base class for all external biomedical evidence adapters."""

    def __init__(
        self,
        provider_name: str,
        mode: AdapterExecutionMode = AdapterExecutionMode.LIVE_API_MODE,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self.provider_name = provider_name
        self.mode = mode
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.snapshot_cache: dict[str, dict[str, Any]] = {}

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search external provider for candidate records."""
        ...

    @abstractmethod
    def fetch(self, source_id: str) -> dict[str, Any]:
        """Fetch raw record payload by provider identifier."""
        ...

    @abstractmethod
    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize raw provider JSON into standard evidence dictionary schema."""
        ...

    @abstractmethod
    def provenance(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Extract request/response provenance & telemetry metadata."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Ping provider endpoint to verify health & availability."""
        ...

    def compute_raw_response_hash(self, payload: dict[str, Any] | str) -> str:
        """Compute canonical SHA-256 digest of raw API response."""
        if isinstance(payload, dict):
            serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            serialized = str(payload).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def sanitize_text_content(self, text: str | None) -> str:
        """Sanitize raw API text content against HTML tags and prompt injection markers."""
        if not text:
            return ""
        # Strip HTML/XML tags
        clean_text = re.sub(r"<[^>]+>", "", str(text))
        # Pass through deterministic security sanitizer
        san_res = sanitize_query(clean_text)
        return san_res.sanitized
