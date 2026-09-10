
import json

from .memory_types import MemoryRecord, MemoryType


class ResearchMemoryStore:
    """Stores persistent research memory. Memory != Evidence."""
    def __init__(self):
        self._records: dict[str, MemoryRecord] = {}

    def add(self, record: MemoryRecord) -> None:
        if record.memory_id in self._records:
            raise ValueError(f"Memory {record.memory_id} already exists.")
        # Deep copy to ensure mutation isolation
        copied = MemoryRecord(
            memory_id=record.memory_id,
            memory_type=record.memory_type,
            provenance=json.loads(json.dumps(record.provenance)),
            metadata=json.loads(json.dumps(record.metadata)),
            created_at=record.created_at
        )
        self._records[record.memory_id] = copied

    def get(self, memory_id: str) -> MemoryRecord:
        if memory_id not in self._records:
            raise KeyError(f"Memory {memory_id} not found.")
        return self._records[memory_id]

    def list_all(self) -> list[MemoryRecord]:
        return list(self._records.values())

    def search(self, memory_type: MemoryType | None = None, **kwargs) -> list[MemoryRecord]:
        results = self.list_all()
        if memory_type:
            results = [r for r in results if r.memory_type == memory_type]
        for k, v in kwargs.items():
            results = [r for r in results if r.metadata.get(k) == v]
        return results

    def serialize(self) -> str:
        raw = [r.to_dict() for r in self._records.values()]
        return json.dumps(raw, sort_keys=True)
