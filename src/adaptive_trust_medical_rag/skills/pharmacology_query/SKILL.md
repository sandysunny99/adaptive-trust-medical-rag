# Pharmacology Query Routing

## Purpose
Wraps EvidenceQueryRouter to classify and route pharmacological queries.

## Inputs / Outputs
- **Input**: Structured `SkillInput` dictionary.
- **Output**: Structured `SkillOutput` dictionary preserving provenance.

## Safety Constraints
- Does NOT modify canonical experiment artifacts.
- Preserves evidence source identity and timestamps.
- Fails closed on invalid inputs.

## Existing Project Implementation Used
- Module: `adaptive_trust_medical_rag.evidence_sources.query_router`
- Class/Function: `EvidenceQueryRouter`

## Version / Status
- Version: 1.0.0
- Status: DEVELOPED
