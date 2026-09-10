"""
Research Harness: Approval Manager

Manages explicit human approval for transitions and experiments.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum


class ApprovalState(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


@dataclass
class ApprovalRecord:
    experiment_id: str
    run_id: str
    state: ApprovalState
    approver: str | None
    rationale: str
    timestamp: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d['state'] = self.state.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'ApprovalRecord':
        return cls(
            experiment_id=data['experiment_id'],
            run_id=data['run_id'],
            state=ApprovalState(data['state']),
            approver=data.get('approver'),
            rationale=data.get('rationale', ''),
            timestamp=data['timestamp']
        )


class ApprovalManager:
    """Manages recording and verifying explicit human approvals."""

    def __init__(self):
        self._records: dict[str, ApprovalRecord] = {}

    def _get_key(self, experiment_id: str, run_id: str) -> str:
        return f"{experiment_id}::{run_id}"

    def request_approval(self, experiment_id: str, run_id: str, rationale: str = "Awaiting human review") -> ApprovalRecord:
        """Initializes an approval request in PENDING state."""
        key = self._get_key(experiment_id, run_id)
        if key in self._records and self._records[key].state in (ApprovalState.APPROVED, ApprovalState.REJECTED):
            raise ValueError(f"Cannot request approval. State is already {self._records[key].state.value}")

        record = ApprovalRecord(
            experiment_id=experiment_id,
            run_id=run_id,
            state=ApprovalState.PENDING,
            approver=None,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._records[key] = record
        return record

    def approve(self, experiment_id: str, run_id: str, approver: str, rationale: str) -> ApprovalRecord:
        """Records an explicit human approval."""
        key = self._get_key(experiment_id, run_id)
        if key not in self._records:
            raise ValueError("No pending approval request found.")

        if self._records[key].state == ApprovalState.APPROVED:
            raise ValueError("Already approved.")

        if self._records[key].state in (ApprovalState.REJECTED, ApprovalState.REVOKED):
            raise ValueError(f"Cannot approve. Current state is {self._records[key].state.value}.")

        record = ApprovalRecord(
            experiment_id=experiment_id,
            run_id=run_id,
            state=ApprovalState.APPROVED,
            approver=approver,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._records[key] = record
        return record

    def reject(self, experiment_id: str, run_id: str, approver: str, rationale: str) -> ApprovalRecord:
        """Records an explicit human rejection."""
        key = self._get_key(experiment_id, run_id)
        if key not in self._records:
            raise ValueError("No pending approval request found.")

        if self._records[key].state in (ApprovalState.APPROVED, ApprovalState.REJECTED, ApprovalState.REVOKED):
            raise ValueError(f"Cannot reject. Current state is {self._records[key].state.value}.")

        record = ApprovalRecord(
            experiment_id=experiment_id,
            run_id=run_id,
            state=ApprovalState.REJECTED,
            approver=approver,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._records[key] = record
        return record

    def revoke(self, experiment_id: str, run_id: str, approver: str, rationale: str) -> ApprovalRecord:
        """Revokes an existing approval."""
        key = self._get_key(experiment_id, run_id)
        if key not in self._records or self._records[key].state != ApprovalState.APPROVED:
            raise ValueError("Can only revoke APPROVED state.")

        record = ApprovalRecord(
            experiment_id=experiment_id,
            run_id=run_id,
            state=ApprovalState.REVOKED,
            approver=approver,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._records[key] = record
        return record

    def get_state(self, experiment_id: str, run_id: str) -> ApprovalRecord | None:
        return self._records.get(self._get_key(experiment_id, run_id))
