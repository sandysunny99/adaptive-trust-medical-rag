# CLAIM VERIFIER V2 AUDIT

**Target:** `src/adaptive_trust_medical_rag/verification/claim_verifier_v2.py`

1. **Inputs**: `answer: str`, `evidence: list[EvidenceChunk]`.
2. **Preprocessing**: Regex-based sentence and clause splitting.
3. **Evidence Checks**: Computes NLI (entailment, contradiction, neutral) for *every* chunk against *every* claim.
4. **Support Checks**: `max_ent > max_con and max_ent > max_neu` -> `SUPPORTED`.
5. **Contradiction**: `max_con > 0.4 and max_ent > 0.4 and max_con - max_ent >= 0.3` -> `CONTRADICTED`.
6. **Trust/Relationship**: NOT consumed.
7. **Provenance**: Computed into `CitationValidation`, but ignored in gating.
8. **Failure Handling**: Catches `NLIInferenceError`, sets chunk scores to `{ent:0, con:0, neu:1.0}`.
