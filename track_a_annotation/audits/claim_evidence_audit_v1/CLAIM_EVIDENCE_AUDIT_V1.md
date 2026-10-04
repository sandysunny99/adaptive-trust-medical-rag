# CLAIM-EVIDENCE CONTROL AUDIT V1

## Executive Summary
This audit evaluated whether the Claim-Evidence Control Layer reliably establishes that generated claims are supported by available evidence. The audit found that while NLI-based textual entailment is implemented, critical gaps exist in provenance verification and trust propagation.

## Key Findings
1. **Provenance Enforcement Gap (P0)**: The `ClaimVerifierV2` evaluates support by scanning all session chunks. If any chunk supports the claim, it is marked `SUPPORTED` and the gate `releases` it, even if the citation `[Source N]` provided by the LLM is completely fabricated or points to an irrelevant chunk. `CitationValidation` is computed but ignored in the `GateDecision`.
2. **Trust Propagation Gap (P1)**: `ClaimVerifierV2` does not receive `trust_score` or `missing_factors`. While the orchestrator filters chunks pre-generation via `EvidenceEligibilityGate`, the post-generation verifier cannot make claim-level decisions based on incomplete trust state.
3. **Claim vs. Relationship Gap (P1)**: Relationship grounding (RG-02) is applied to chunks pre-generation, but the verifier does not structurally validate that the *generated claim* preserves the authorized relationship. It relies solely on flat text NLI.

## Current Validation Level
- Claim Representation: IMPLEMENTED
- Evidence Linkage: IMPLEMENTED_UNTESTED (Fails provenance constraint)
- NLI Contradiction: IMPLEMENTED
- Output Gating: IMPLEMENTED (but flawed due to provenance gap)

## Conclusion
The system operates at a chunk-availability level rather than strict claim-provenance level. An unsupported citation can reach final output if the text happens to be entailed by *any* chunk in context.
