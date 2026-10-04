"""
Context Store — L0/L1/L2 hierarchical context records.

Ponytail: dataclass + dict, no ORM, no custom serializer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ContextLevel(Enum):
    L0 = "L0"  # short abstract / relevance snippet
    L1 = "L1"  # structured overview (title, source, entities, provenance)
    L2 = "L2"  # full evidence text


@dataclass
class ContextMetadata:
    estimated_tokens_l0: int | None = None
    estimated_tokens_l1: int | None = None
    estimated_tokens_l2: int | None = None
    compression_ratio: float | None = None

@dataclass
class ContextRecord:
    """One unit of context derived from pharmacology evidence.

    Provenance is mandatory — records without it are rejected.
    Content must never silently overwrite source evidence.
    """
    record_id: str
    level: ContextLevel
    content: str
    provenance: dict[str, Any]  # source, document_id, timestamp, …
    metadata: ContextMetadata | None = None

    def __post_init__(self) -> None:
        if not self.provenance:
            raise ValueError(f"ContextRecord {self.record_id}: provenance is required.")
        if not self.record_id:
            raise ValueError("record_id must be non-empty.")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        if self.metadata is not None:
            d["metadata"] = asdict(self.metadata)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextRecord":
        metadata_data = data.get("metadata")
        metadata = ContextMetadata(**metadata_data) if metadata_data else None
        return cls(
            record_id=data["record_id"],
            level=ContextLevel(data["level"]),
            content=data["content"],
            provenance=data["provenance"],
        )


class ContextStore:
    """Stores and retrieves ContextRecords, keyed by record_id.

    Isolation guarantee: records are stored by value (no reference aliases
    to source evidence dicts) — callers cannot mutate evidence via this store.
    """

    def __init__(self) -> None:
        self._store: dict[str, ContextRecord] = {}

    def add(self, record: ContextRecord) -> None:
        """Add a record. Raises on missing provenance (enforced by ContextRecord)."""
        # Store a deep copy of provenance so callers cannot mutate evidence via this dict.
        safe = ContextRecord(
            record_id=record.record_id,
            level=record.level,
            content=record.content,
            provenance=json.loads(json.dumps(record.provenance)),  # deep copy
        )
        self._store[record.record_id] = safe

    def get(self, record_id: str) -> ContextRecord:
        if record_id not in self._store:
            raise KeyError(f"Context record not found: {record_id}")
        return self._store[record_id]

    def get_level(self, level: ContextLevel) -> list[ContextRecord]:
        return [r for r in self._store.values() if r.level == level]

    def load_level(self, record_id: str, level: ContextLevel) -> str:
        """Progressive load: return content only if record is at requested level."""
        rec = self.get(record_id)
        if rec.level != level:
            raise ValueError(
                f"Record {record_id} is at {rec.level.value}, not {level.value}."
            )
        return rec.content

    def list_ids(self) -> list[str]:
        return list(self._store.keys())
