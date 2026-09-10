"""
Research Harness: Gate Engine

Evaluates a deterministic sequence of named gates, stopping on failures.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class GateStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


@dataclass
class GateResult:
    gate_id: str
    description: str
    status: GateStatus
    evidence: dict[str, Any]
    timestamp: str
    blocking: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d


@dataclass
class GateReport:
    overall_status: GateStatus
    results: list[GateResult]
    failed_gate_id: str | None

    def to_dict(self) -> dict:
        return {
            "overall_status": self.overall_status.value,
            "results": [r.to_dict() for r in self.results],
            "failed_gate_id": self.failed_gate_id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


class GateEngine:
    """Evaluates a list of named gates with fail-closed semantics."""

    def __init__(self):
        self._gates: list[tuple[str, str, bool, Callable[[], dict[str, Any]]]] = []

    def register_gate(self, gate_id: str, description: str, blocking: bool, evaluation_fn: Callable[[], dict[str, Any]]) -> None:
        """
        Registers a gate. The evaluation_fn should return a dict with:
        {'passed': bool, 'evidence': dict}
        """
        self._gates.append((gate_id, description, blocking, evaluation_fn))

    def evaluate(self) -> GateReport:
        """
        Evaluates registered gates in order. 
        Stops and reports FAIL if any blocking gate fails.
        """
        results = []
        overall_status = GateStatus.PASS
        failed_gate_id = None

        for gate_id, desc, blocking, eval_fn in self._gates:
            if overall_status == GateStatus.FAIL:
                # Skip subsequent gates once a blocking failure occurred
                results.append(GateResult(
                    gate_id=gate_id,
                    description=desc,
                    status=GateStatus.SKIPPED,
                    evidence={"reason": f"Skipped due to prior failure in {failed_gate_id}"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    blocking=blocking
                ))
                continue

            try:
                fn_result = eval_fn()
                passed = bool(fn_result.get('passed', False))
                evidence = fn_result.get('evidence', {})
            except Exception as e:
                passed = False
                evidence = {"error": str(e), "type": "UNHANDLED_EXCEPTION"}

            status = GateStatus.PASS if passed else GateStatus.FAIL

            results.append(GateResult(
                gate_id=gate_id,
                description=desc,
                status=status,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc).isoformat(),
                blocking=blocking
            ))

            if status == GateStatus.FAIL and blocking:
                overall_status = GateStatus.FAIL
                failed_gate_id = gate_id

        return GateReport(
            overall_status=overall_status,
            results=results,
            failed_gate_id=failed_gate_id
        )
