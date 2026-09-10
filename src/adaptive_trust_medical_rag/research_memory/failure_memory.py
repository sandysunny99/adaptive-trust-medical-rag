
import uuid
from typing import Any

from .memory_store import ResearchMemoryStore
from .memory_types import MemoryRecord, MemoryType


class FailureMemory:
    """Records known failures/blockers. No automatic retry or mutation."""
    def __init__(self, store: ResearchMemoryStore):
        self.store = store

    def record_failure(self, failure_type: str, details: dict[str, Any], provenance: dict[str, Any]) -> MemoryRecord:
        rec = MemoryRecord(
            memory_id=f"fail_{uuid.uuid4().hex[:8]}",
            memory_type=MemoryType.FAILURE,
            provenance=provenance,
            metadata={"failure_type": failure_type, "details": details}
        )
        self.store.add(rec)
        return rec
