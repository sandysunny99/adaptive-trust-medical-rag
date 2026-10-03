# Canonical Relationship Identity Gap Analysis

## 1. Input / Representation Gap
- **Finding:** The Canonical RxCUI (provided by `DrugNormalizer`) is downcast to a `list[str]` array of names immediately inside `rag_orchestrator.py`. 
- **Impact:** `RG-02` re-computes drug occurrences via regex `_extract_entities_simple()` instead of using the trusted canonical graph. 

## 2. Propagation Gap
- **Finding:** `RG-02` creates an `entity_alignment` dictionary tracking the string endpoints of the relationship. However, when the Orchestrator instantiates `EvidenceChunk` objects, it only passes the status: `grounding_states[chunk_id].status.name`.
- **Impact:** By the time evidence reaches the post-generation `ClaimVerifierV2`, there is absolutely no record of *which* drugs or *which* relationships were grounded.

## 3. Final Claim Binding Gap
- **Finding:** `ClaimVerifierV2` uses text-based Natural Language Inference (NLI) to compute an entailment score. It never compares the canonical subject/predicate/object of the claim against the source evidence.
- **Impact:** An LLM hallucinating the wrong drug name (but maintaining similar text phrasing) or hallucinating the directionality of the interaction (A increases B instead of B increases A) could fool the textual NLI and pass the Answer Safety Gate.

## Final Classification
**ARCHITECTURAL_GAP** - The system is fundamentally missing the data structures required to carry semantic relationship identities across the execution boundary and perform structured semantic verification at the final gate.
