"""
Retrieval Trace — records how context was selected for a query/session.

Ponytail: append-only list of dataclass events. No DB, no frameworks.
Security: must not record raw evidence text or PHI — only references.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TraceEvent:
    operation: str       # e.g. "resource_discovery", "level_selection", "trust_eval"
    resource_id: str
    selected_level: str  # L0/L1/L2 or "N/A"
    reason: str
    rank: int | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RetrievalTrace:
    """Records how a piece of context was found and selected.

    Never stores raw query text from user input (privacy) or full document
    content (keeps traces small). Only references and decisions are stored.
    """

    def __init__(self, session_id: str, query_hash: str) -> None:
        self.trace_id = str(uuid.uuid4())
        self.session_id = session_id
        self.query_hash = query_hash  # hash only, never raw query
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._events: list[TraceEvent] = []

    def record(
        self,
        operation: str,
        resource_id: str,
        selected_level: str,
        reason: str,
        rank: int | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> None:
        self._events.append(
            TraceEvent(
                operation=operation,
                resource_id=resource_id,
                selected_level=selected_level,
                reason=reason,
                rank=rank,
                provenance=provenance or {},
            )
        )

    def events(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "query_hash": self.query_hash,
            "created_at": self.created_at,
            "events": self.events(),
        }
