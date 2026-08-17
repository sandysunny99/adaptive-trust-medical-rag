"""Local drug entity cache — brand/synonym → generic/RxCUI mapping.

Loaded from `data/drug_entity_cache.json` at startup.
Falls back to an empty dict if the file is missing (graceful degradation).

Cache format (each entry):
    {
      "generic_name": "warfarin",
      "rxcui": "11289",
      "brand_name": "Coumadin",
      "formulation": null
    }
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from adaptive_trust_medical_rag.normalization.drug_normalizer import DrugEntity

logger = logging.getLogger(__name__)


def _find_project_root() -> Path:
    """Walk up from this file until we find pyproject.toml (project root marker)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Final fallback: cwd
    return Path.cwd()


_DEFAULT_CACHE_PATH = _find_project_root() / "data" / "drug_entity_cache.json"


class EntityCache:
    """In-memory drug entity cache backed by a JSON file."""

    def __init__(self, data: dict[str, dict[str, Any]]) -> None:
        # Normalise all keys to lowercase for case-insensitive lookup
        self._data: dict[str, dict[str, Any]] = {k.lower(): v for k, v in data.items()}

    @classmethod
    def load_default(cls) -> "EntityCache":
        return cls.from_file(_DEFAULT_CACHE_PATH)

    @classmethod
    def from_file(cls, path: Path) -> "EntityCache":
        """Load cache from JSON. Returns empty cache if file missing."""
        if not path.exists():
            logger.warning("Drug entity cache not found at %s — using empty cache.", path)
            return cls({})
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded %d drug entity cache entries from %s.", len(data), path)
            return cls(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load drug entity cache from %s: %s", path, exc)
            return cls({})

    def lookup(self, name: str) -> dict[str, Any] | None:
        """Case-insensitive lookup. Returns the cache entry dict or None."""
        return self._data.get(name.lower().strip())

    def store(self, name: str, entity: "DrugEntity") -> None:
        """Add a resolved entity to the in-memory cache (write-through not implemented yet)."""
        self._data[name.lower().strip()] = {
            "generic_name": entity.generic_name,
            "rxcui": entity.rxcui,
            "brand_name": entity.brand_name,
            "formulation": entity.formulation,
        }

    def __len__(self) -> int:
        return len(self._data)
