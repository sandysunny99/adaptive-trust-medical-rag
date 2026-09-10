
import uuid
from typing import Any

from .memory_store import ResearchMemoryStore
from .memory_types import MemoryRecord, MemoryType


class SessionMemory:
    """Records session-scoped working memory. Isolated between sessions."""
    def __init__(self, store: ResearchMemoryStore):
        self.store = store

    def record_session_state(self, session_id: str, state_summary: dict[str, Any], provenance: dict[str, Any]) -> MemoryRecord:
        rec = MemoryRecord(
            memory_id=f"sess_{uuid.uuid4().hex[:8]}",
            memory_type=MemoryType.SESSION,
            provenance=provenance,
            metadata={"session_id": session_id, "state": state_summary}
        )
        self.store.add(rec)
        return rec
