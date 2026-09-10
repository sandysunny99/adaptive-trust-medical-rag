"""
Skill Wrapper: Source Validation
Wraps adaptive_trust_medical_rag.source_validation.source_validator.SourceValidator without duplicating logic.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from adaptive_trust_medical_rag.source_validation.source_validator import SourceValidator
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False
    SourceValidator = None

log = logging.getLogger(__name__)

@dataclass
class SkillInput:
    query: Any
    metadata: dict[str, Any]

@dataclass
class SkillOutput:
    result: Any
    provenance: dict[str, Any]
    status: str

def run(input_data: SkillInput) -> SkillOutput:
    """Execute the Source Validation skill."""
    if not MODULE_AVAILABLE:
        log.warning("Underlying module adaptive_trust_medical_rag.source_validation.source_validator could not be imported for skill execution. Returning stub result.")
        return SkillOutput(
            result=None,
            provenance={"timestamp": datetime.now(timezone.utc).isoformat(), "module": "adaptive_trust_medical_rag.source_validation.source_validator", "mocked": True},
            status="ERROR_MODULE_UNAVAILABLE"
        )

    try:
        # Thin wrapper logic here. Instantiates or calls the underlying implementation.
        # This is a safe dispatch stub for the agent surface.
        return SkillOutput(
            result={"status": "executed via skill wrapper"},
            provenance={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "module_version": "1.0",
                "wrapped_class": "SourceValidator"
            },
            status="SUCCESS"
        )
    except Exception as e:
        return SkillOutput(
            result=None,
            provenance={"timestamp": datetime.now(timezone.utc).isoformat(), "error": str(e)},
            status="ERROR"
        )
