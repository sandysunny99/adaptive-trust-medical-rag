"""
Resource Manager — register and look up typed resources.

Ponytail: plain Enum + dataclass dict. No registry framework.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ResourceType(Enum):
    EVIDENCE = "EVIDENCE"   # pharmacology documents from adapters
    SKILL = "SKILL"         # callable skill wrappers (Phase 9)
    RESEARCH = "RESEARCH"   # experiment/decision records
    SESSION = "SESSION"     # temporary session data
    EXPERIMENT = "EXPERIMENT"


@dataclass
class ResourceEntry:
    resource_id: str
    resource_type: ResourceType
    description: str
    path: str  # logical path, e.g. "evidence/pubmed/PMC12345"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["resource_type"] = self.resource_type.value
        return d


class ResourceManager:
    """Register and look up logical resources.

    Does NOT store evidence content — only references/metadata.
    Separation: ResourceManager knows WHERE evidence lives, not WHAT it says.
    """

    def __init__(self) -> None:
        self._resources: dict[str, ResourceEntry] = {}

    def register(
        self,
        resource_id: str,
        resource_type: ResourceType,
        description: str,
        path: str,
        metadata: dict[str, Any] | None = None,
    ) -> ResourceEntry:
        if resource_id in self._resources:
            raise ValueError(f"Resource already registered: {resource_id}")
        entry = ResourceEntry(
            resource_id=resource_id,
            resource_type=resource_type,
            description=description,
            path=path,
            metadata=metadata or {},
        )
        self._resources[resource_id] = entry
        return entry

    def get(self, resource_id: str) -> ResourceEntry:
        if resource_id not in self._resources:
            raise KeyError(f"Resource not found: {resource_id}")
        return self._resources[resource_id]

    def filter_by_type(self, resource_type: ResourceType) -> list[ResourceEntry]:
        return [r for r in self._resources.values() if r.resource_type == resource_type]

    def list_ids(self) -> list[str]:
        return list(self._resources.keys())
