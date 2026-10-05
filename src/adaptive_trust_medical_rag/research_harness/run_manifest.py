"""
Research Harness: Run Manifest

Defines a structured, deterministically serializable representation of an experiment run.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class RunState(Enum):
    DESIGNED = "DESIGNED"
    FROZEN = "FROZEN"
    PREFLIGHT = "PREFLIGHT"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    CHECKPOINTED = "CHECKPOINTED"
    COMPLETED = "COMPLETED"
    ANALYZED = "ANALYZED"
    LOCKED = "LOCKED"

@dataclass
class ExperimentCheckpoint:
    checkpoint_id: str
    run_id: str
    last_completed_case: int
    total_cases: int
    state: dict[str, Any]
    timestamp: str

@dataclass
class RunManifest:
    """Represents a complete, deterministic record of an experiment run."""
    experiment_id: str
    run_id: str
    timestamp: str
    code_version: str
    configuration: dict[str, Any]
    inputs: dict[str, Any]
    artifacts: list[str]
    artifact_hashes: dict[str, str]
    environment: dict[str, str]
    outputs: dict[str, Any]
    metrics: dict[str, Any]
    gate_results: dict[str, Any]
    approval_state: str
    status: str
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'RunManifest':
        # Ensure required fields are present; failure here means missing required field
        return cls(
            experiment_id=data['experiment_id'],
            run_id=data['run_id'],
            timestamp=data['timestamp'],
            code_version=data['code_version'],
            configuration=data.get('configuration', {}),
            inputs=data.get('inputs', {}),
            artifacts=data.get('artifacts', []),
            artifact_hashes=data.get('artifact_hashes', {}),
            environment=data.get('environment', {}),
            outputs=data.get('outputs', {}),
            metrics=data.get('metrics', {}),
            gate_results=data.get('gate_results', {}),
            approval_state=data.get('approval_state', 'PENDING'),
            status=data.get('status', 'UNKNOWN'),
            notes=data.get('notes', '')
        )

    def to_json(self) -> str:
        """Serializes the manifest deterministically."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'RunManifest':
        return cls.from_dict(json.loads(json_str))
