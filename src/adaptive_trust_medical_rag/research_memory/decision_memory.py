
import uuid
from typing import Any

from .memory_store import ResearchMemoryStore
from .memory_types import MemoryRecord, MemoryType


class DecisionMemory:
    """Records research/agent decisions including rationale and metadata."""
    def __init__(self, store: ResearchMemoryStore):
        self.store = store

    def record_decision(self, rationale: str, decision_context: dict[str, Any], provenance: dict[str, Any]) -> MemoryRecord:
        rec = MemoryRecord(
            memory_id=f"dec_{uuid.uuid4().hex[:8]}",
            memory_type=MemoryType.DECISION,
            provenance=provenance,
            metadata={"rationale": rationale, "context": decision_context}
        )
        self.store.add(rec)
        return rec
