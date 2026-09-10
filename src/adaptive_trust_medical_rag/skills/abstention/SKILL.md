# Controlled Abstention

## Purpose
Wraps EvidenceEligibilityGate to enforce system abstention thresholds.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.orchestrator.rag_orchestrator`
- Class/Function: `EvidenceEligibilityGate`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
