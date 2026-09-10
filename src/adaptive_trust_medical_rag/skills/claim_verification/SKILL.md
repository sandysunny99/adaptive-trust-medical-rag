# Claim Verification

## Purpose
Wraps AnswerSafetyGate to verify LLM claims against retrieved evidence.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.verification.claim_verifier`
- Class/Function: `AnswerSafetyGate`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
