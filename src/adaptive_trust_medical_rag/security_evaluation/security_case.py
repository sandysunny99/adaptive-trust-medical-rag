import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AttackFamily(Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    RETRIEVAL_POISONING = "RETRIEVAL_POISONING"
    BOUNDARY_VIOLATION = "BOUNDARY_VIOLATION"
    PROVENANCE_ATTACK = "PROVENANCE_ATTACK"
    BENIGN_CONTROL = "BENIGN_CONTROL"


class ExpectedOutcome(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FLAG = "FLAG"
    ESCALATE = "ESCALATE"
    UNAUTHORIZED_ACTION_REJECTED = "UNAUTHORIZED_ACTION_REJECTED"


class EvaluationCondition(Enum):
    BASELINE = "BASELINE"
    HARDENED = "HARDENED"


@dataclass
class SecurityCase:
    case_id: str
    attack_family: AttackFamily
    attack_subtype: str
    payload: str
    target_component: str
    expected_security_property: str
    expected_outcome: ExpectedOutcome
    provenance_fixture: dict[str, Any]
    requires_provenance_preservation: bool = False
    requires_authorization_check: bool = False
    requested_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def case_input_hash(self) -> str:
        """Deterministic SHA-256 fingerprint of the full case input.

        Covers every field that defines the evaluation input.
        BASELINE and HARDENED must produce identical hashes for the
        same SecurityCase instance.
        """
        canonical = json.dumps(
            {
                "case_id": self.case_id,
                "attack_family": self.attack_family.value,
                "attack_subtype": self.attack_subtype,
                "payload": self.payload,
                "target_component": self.target_component,
                "expected_security_property": self.expected_security_property,
                "expected_outcome": self.expected_outcome.value,
                "provenance_fixture": self.provenance_fixture,
                "requires_provenance_preservation": self.requires_provenance_preservation,
                "requires_authorization_check": self.requires_authorization_check,
                "requested_action": self.requested_action,
                "metadata": self.metadata,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()
