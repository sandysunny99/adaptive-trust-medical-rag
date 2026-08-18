"""Verification package for adaptive-trust-medical-rag."""

from adaptive_trust_medical_rag.verification.claim_verifier import (
    ALIGNMENT_THRESHOLD,
    ALPHA,
    BETA,
    GAMMA,
    AlignmentResult,
    AnswerSafetyGate,
    AtomicClaim,
    ContradictionFlag,
    EvidenceChunk,
    GateDecision,
    VerificationReport,
    align_claims_to_evidence,
    decompose_into_claims,
    detect_contradictions,
)

__all__ = [
    "ALIGNMENT_THRESHOLD",
    "ALPHA",
    "BETA",
    "GAMMA",
    "AlignmentResult",
    "AnswerSafetyGate",
    "AtomicClaim",
    "ContradictionFlag",
    "EvidenceChunk",
    "GateDecision",
    "VerificationReport",
    "align_claims_to_evidence",
    "decompose_into_claims",
    "detect_contradictions",
]
