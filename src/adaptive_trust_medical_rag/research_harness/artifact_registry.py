"""
Research Harness: Artifact Registry

Manages deterministic artifact registration and integrity verification via SHA-256.
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class ArtifactMetadata:
    artifact_id: str
    path: str
    sha256: str
    size_bytes: int
    created_at: str
    registered_at: str
    experiment_id: str
    role: str
    frozen: bool
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ArtifactMetadata':
        return cls(**data)


class ArtifactRegistry:
    """Central registry for tracking experiment artifacts and verifying hashes."""

    def __init__(self, registry_path: Path | None = None):
        self._artifacts: dict[str, ArtifactMetadata] = {}
        self._registry_path = registry_path or Path("experiments/manifests/artifact_registry.json")
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.load()

    def calculate_hash(self, file_path: Path) -> str:
        """Calculates the SHA-256 hash of a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")
        return hashlib.sha256(file_path.read_bytes()).hexdigest().upper()

    def register(
        self,
        artifact_id: str,
        file_path: Path,
        experiment_id: str,
        role: str,
        frozen: bool = False,
        notes: str = ""
    ) -> ArtifactMetadata:
        """Registers a new artifact or updates an existing one if not frozen."""
        if artifact_id in self._artifacts and self._artifacts[artifact_id].frozen:
            raise ValueError(f"Artifact {artifact_id} is frozen and cannot be re-registered.")

        if not file_path.exists():
            raise FileNotFoundError(f"Cannot register missing artifact: {file_path}")

        stat = file_path.stat()
        file_hash = self.calculate_hash(file_path)

        now = datetime.now(timezone.utc).isoformat()
        # Fallback for created_at if system doesn't provide precise creation time
        created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()

        meta = ArtifactMetadata(
            artifact_id=artifact_id,
            path=str(file_path.as_posix()),
            sha256=file_hash,
            size_bytes=stat.st_size,
            created_at=created_at,
            registered_at=now,
            experiment_id=experiment_id,
            role=role,
            frozen=frozen,
            notes=notes
        )

        self._artifacts[artifact_id] = meta
        self.export()
        return meta

    def verify(self, artifact_id: str) -> bool:
        """Verifies the current file hash matches the registered hash. Fails closed."""
        if artifact_id not in self._artifacts:
            log.error(f"Verification failed: Artifact {artifact_id} not in registry.")
            return False

        meta = self._artifacts[artifact_id]
        file_path = Path(meta.path)

        if not file_path.exists():
            log.error(f"Verification failed: Artifact file missing for {artifact_id} at {file_path}")
            return False

        current_hash = self.calculate_hash(file_path)
        if current_hash != meta.sha256:
            log.error(f"Verification failed: Hash mismatch for {artifact_id}. Expected {meta.sha256}, got {current_hash}")
            return False

        return True

    def get(self, artifact_id: str) -> ArtifactMetadata | None:
        return self._artifacts.get(artifact_id)

    def list(self) -> list[ArtifactMetadata]:
        return list(self._artifacts.values())

    def export(self) -> None:
        """Exports the registry to deterministic JSON."""
        data = {k: v.to_dict() for k, v in sorted(self._artifacts.items())}
        self._registry_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')

    def load(self) -> None:
        """Loads the registry from disk if it exists."""
        if self._registry_path.exists():
            try:
                data = json.loads(self._registry_path.read_text(encoding='utf-8'))
                self._artifacts = {k: ArtifactMetadata.from_dict(v) for k, v in data.items()}
            except json.JSONDecodeError as e:
                log.error(f"Failed to load registry: {e}")
                raise ValueError("Registry JSON is corrupt.") from e
