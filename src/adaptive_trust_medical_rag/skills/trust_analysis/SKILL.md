# Adaptive Trust Analysis

## Purpose
Wraps AdaptiveTrustScorer to calculate dynamic trust scores for retrieved evidence.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.trust_scoring.trust_scorer`
- Class/Function: `AdaptiveTrustScorer`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
