# Source Validation

## Purpose
Wraps SourceValidator to determine evidence authority, freshness, and provenance.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.source_validation.source_validator`
- Class/Function: `SourceValidator`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
