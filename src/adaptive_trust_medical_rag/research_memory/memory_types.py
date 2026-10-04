
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MemoryType(Enum):
    SESSION = "SESSION"
    EXPERIMENT = "EXPERIMENT"
    DECISION = "DECISION"
    FAILURE = "FAILURE"

class LifecycleState(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"

@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: MemoryType
    provenance: dict[str, Any]
    metadata: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0.0"
    schema_version: str = "1.0"
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE

    def __post_init__(self):
        if not isinstance(self.provenance, dict) or not self.provenance:
            raise ValueError("Provenance must be a non-empty dictionary.")
        if not any(k in self.provenance for k in ("source", "origin", "reference")):
            raise ValueError("Provenance must contain a meaningful origin/reference field (e.g., 'source', 'origin', 'reference').")

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "version": self.version,
            "schema_version": self.schema_version,
            "lifecycle_state": self.lifecycle_state.value
        }
