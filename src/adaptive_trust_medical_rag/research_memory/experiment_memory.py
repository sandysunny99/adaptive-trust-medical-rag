
import uuid
from typing import Any

from .memory_store import ResearchMemoryStore
from .memory_types import MemoryRecord, MemoryType


class ExperimentMemory:
    """Records experiment configurations/observations. References only; must not modify artifacts."""
    def __init__(self, store: ResearchMemoryStore):
        self.store = store

    def record_observation(self, run_id: str, observation: dict[str, Any], provenance: dict[str, Any]) -> MemoryRecord:
        rec = MemoryRecord(
            memory_id=f"exp_{uuid.uuid4().hex[:8]}",
            memory_type=MemoryType.EXPERIMENT,
            provenance=provenance,
            metadata={"run_id": run_id, "observation": observation}
        )
        self.store.add(rec)
        return rec
