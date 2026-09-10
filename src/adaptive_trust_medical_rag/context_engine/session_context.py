"""
Session Context — transient context assembled for one agent interaction.

Ponytail: one dataclass, one uuid, stdlib only. Not persisted automatically.
SessionContext is task-scoped and must not leak into other sessions.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .context_store import ContextStore
from .resource_manager import ResourceManager
from .retrieval_trace import RetrievalTrace


@dataclass
class SessionContext:
    """Temporary context for a single query/session.

    Isolation: each session owns its own ContextStore, ResourceManager, and
    RetrievalTrace. Closing a session does not write to persistent evidence.
    Trust and verification metadata are DISPLAYED here, not computed here.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_hash: str = ""          # hash of original query, never raw text
    query_type: str = ""          # e.g. "DDI", "ADE", "mechanism"
    resolved_entities: list[str] = field(default_factory=list)
    selected_resources: list[str] = field(default_factory=list)
    selected_evidence: list[str] = field(default_factory=list)  # doc IDs only
    trust_metadata: dict[str, Any] = field(default_factory=dict)
    security_metadata: dict[str, Any] = field(default_factory=dict)
    verification_metadata: dict[str, Any] = field(default_factory=dict)
    closed: bool = False

    def __post_init__(self) -> None:
        self.store = ContextStore()
        self.resources = ResourceManager()
        self.trace = RetrievalTrace(self.session_id, self.query_hash)

    def close(self) -> None:
        """Mark session closed. Contents should not be read after close."""
        self.closed = True

    def assert_open(self) -> None:
        if self.closed:
            raise RuntimeError(f"Session {self.session_id} is already closed.")

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "query_hash": self.query_hash,
            "query_type": self.query_type,
            "resolved_entities": self.resolved_entities,
            "selected_resources": self.selected_resources,
            "selected_evidence": self.selected_evidence,
            "trust_metadata": self.trust_metadata,
            "security_metadata": self.security_metadata,
            "verification_metadata": self.verification_metadata,
            "trace": self.trace.to_dict(),
            "closed": self.closed,
        }
