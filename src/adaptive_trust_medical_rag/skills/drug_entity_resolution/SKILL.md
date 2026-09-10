# Drug Entity Resolution

## Purpose
Wraps DrugNormalizer to resolve raw drug mentions into canonical RxNorm entities.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.normalization.drug_normalizer`
- Class/Function: `DrugNormalizer`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
