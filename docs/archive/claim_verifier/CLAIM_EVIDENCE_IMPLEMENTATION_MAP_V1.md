# CLAIM_EVIDENCE_IMPLEMENTATION_MAP_V1

## Overview
This map details the post-generation Answer Safety Gate implementation within the Adaptive Trust-Aware Medical RAG orchestrator.

## Runtime Entry Point
The Answer Safety Gate is instantiated and invoked within `src/adaptive_trust_medical_rag/verification/claim_verifier.py` via the `AnswerSafetyGate` class. It is called by the `AdaptiveTrustRAGOrchestrator` after the LLM generates the initial response.

## Execution Flow
1. **User Query** → Processed by `AdaptiveTrustRAGOrchestrator`
2. **Retrieval** → Hybrid retrieval or Cognee adapter fetches chunks.
3. **Evidence Pack** → Formed after `EvidenceEligibilityGate` (filtering untrusted/poisoned chunks).
4. **Generation** → LLM constructs the answer from the evidence pack.
5. **Claim Extraction** (`decompose_into_claims`) → Splits generated answer by sentence boundaries via regex (`(?<=[.!?])\s+(?=[A-Z])`). Extracts citation markers and drug entities via regex.
6. **Claim Verification** (`align_claims_to_evidence`) → For each extracted atomic claim, computes lexical alignment against all evidence chunks using a Jaccard-like overlap of content words (length >= 4). If `score >= ALIGNMENT_THRESHOLD` (0.70), it is marked grounded.
7. **Citation Verification** → Verifies if parsed `[Source N]` IDs physically map to a retrieved chunk, and checks if that chunk's alignment score >= threshold.
8. **Contradiction Detection** (`detect_contradictions`) → Applies a heuristic regex-based Natural Language Inference (NLI) search. If the claim has a "positive" pattern and the evidence has a "negative" pattern, it flags a contradiction.
9. **Final Authorization / Abstention** (`verify`) → Computes a confidence score based on grounding ratio, mean citation trust, and contradiction penalty. Decision routed to:
   - `GateDecision.release` (confidence >= threshold, all claims grounded)
   - `GateDecision.qualify` (confidence < threshold or minor ungrounded claims; modifies string directly)
   - `GateDecision.abstain` (critical ungrounded claims or contradiction + low confidence)
