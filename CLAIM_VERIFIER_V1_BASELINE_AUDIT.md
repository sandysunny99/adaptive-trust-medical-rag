# CLAIM_VERIFIER_V1_BASELINE_AUDIT

## Overview
This audit inspects the current `ClaimVerifierV1` implementation residing in `src/adaptive_trust_medical_rag/verification/claim_verifier.py`.

## Current API & Integration
- **Entry Point:** `AnswerSafetyGate.verify(answer: str, evidence: list[EvidenceChunk]) -> VerificationReport`
- **Integration:** Invoked by `AdaptiveTrustRAGOrchestrator.query` as the final Answer Safety Gate post-generation.

## Current Data Structures
- `EvidenceChunk`: Represents a retrieved chunk (`chunk_id`, `text`, `source_authority`, `citation_index`).
- `AtomicClaim`: Represents an extracted claim (`text`, `claim_index`, `citation_ids`, `is_critical`, `drug_entities`).
- `AlignmentResult`: Maps an `AtomicClaim` to an `EvidenceChunk`, scoring alignment via `alignment_score` and providing a binary `is_grounded` flag.
- `ContradictionFlag`: Captures any detected regex contradictions.
- `VerificationReport`: Final output aggregating alignments, contradictions, confidence, and `GateDecision` (`release`, `qualify`, `abstain`).

## Decomposition Logic
Implemented in `decompose_into_claims`:
- Splits the LLM-generated string on sentence boundaries using the regex `(?<=[.!?])\s+(?=[A-Z])`.
- Citation IDs (`[Source N]`) and drug names (`_DRUG_DOSE_RE`) are extracted.
- Criticality is marked using static regex on unsafe absolute language (e.g., "100%", "never").

## Evidence Alignment Logic
Implemented in `_alignment_score`:
- Tokenizes both the claim and chunk text into lowercase words.
- Filters out words shorter than 4 characters (crude stopword removal).
- Computes Jaccard overlap: `len(overlap) / len(claim_tokens)`.
- If the overlap exceeds `ALIGNMENT_THRESHOLD` (0.70), the claim is marked grounded.

## Contradiction Detection Logic
Implemented in `detect_contradictions`:
- Evaluates the claim against predefined heuristic positive/negative regex tuples (`_NEGATION_SEEDS`).
- If a claim matches the positive pattern and the evidence matches the negative pattern (e.g., "causes" vs "does not cause"), a `ContradictionFlag` is triggered.

## Output States
- The `is_grounded` flag is strictly binary (True/False). 
- There is no native support for `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `INSUFFICIENT_EVIDENCE`, or `AMBIGUOUS`.

## Conclusion
V1 functions exclusively as a heuristic, lexical verification gate. It must remain untouched for future ablation tests while V2 (Semantic NLI) is developed.
