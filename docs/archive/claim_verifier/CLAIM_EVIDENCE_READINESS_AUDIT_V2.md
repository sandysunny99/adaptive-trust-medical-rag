# CLAIM_EVIDENCE_READINESS_AUDIT_V2

## Overview
This audit establishes the readiness of the Claim-Evidence Verifier V2 for component evaluation.

## V1 Baseline Audit & V2 Spec
The V1 verifier (`claim_verifier.py`) was successfully audited (`CLAIM_VERIFIER_V1_BASELINE_AUDIT.md`), confirming its reliance on heuristic string matching and regex logic. 

The V2 verifier semantic contract (`CLAIM_VERIFIER_V2_SPEC.md`) was drafted to demand genuine NLI (entailment, contradiction, neutral) evaluation capabilities that respect pharmacological scope and bounded-negative logic.

## NLI Model Provenance Block
During Phase 3 (NLI Model Selection), an inspection of the project's model cache and offline manifests determined that no appropriate NLI model has been provisioned. The available local models (BGE-small for embeddings, GLiNER for NER) are incapable of outputting the semantic logits required to satisfy the V2 contract.

As per the non-negotiable research rules, the development of V2 was halted prior to implementation. A formal proposal (`CLAIM_VERIFIER_V2_MODEL_SELECTION_PROPOSAL.md`) has been generated to request authorization for an NLI cross-encoder model.

## Final Decision
**CLAIM_VERIFIER_V2_REQUIRES_MODEL_APPROVAL**

No code has been written for V2, and V1 remains completely untouched. The evaluation cannot proceed until an NLI model is formally approved, provisioned into the local cache, and integrated into the V2 architecture.
