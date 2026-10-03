# Canonical Relationship Identity Audit Findings

## 1. Finding: Early Downcasting of Canonical Entity Data
The `DrugNormalizer` is correctly implemented to resolve complex textual drug mentions into RxCUI-backed `DrugEntity` objects using local cache, RxNorm Exact, and RxNorm Approximate lookups. However, in `rag_orchestrator.py`, this structured data is immediately discarded when `normalize()` returns, or is coerced into, a `list[str]`. This is an input representation gap.

## 2. Finding: RG-02 Relies on Fallback String Regex
Because the orchestrator fails to propagate the RxCUI, `relationship_grounding_v2.py` employs a fallback method (`_extract_entities_simple`) relying on regex matching of drug string suffixes (`-statin`, `-mab`, `aspirin`, etc.) to find endpoints. It does not use the canonical RxCUI mapping.

## 3. Finding: Loss of Scope Context in Evidence Chunking
`RG-02` processes candidates and creates a `GroundingDecision` that includes an `entity_alignment` dictionary tracking the string entities found. When the orchestrator maps this to an `EvidenceChunk`, it explicitly drops the `entity_alignment` data and only carries forward the string name of the status (`grounding_states[chunk_id].status.name`). The identity of the relationship is erased at this boundary.

## 4. Finding: Verifier Relies Solely on Textual NLI
The `ClaimVerifierV2` uses `_evaluate_pair(chunk.text, claim.text)` to generate NLI probabilities (entailment, contradiction, neutral). It never attempts to parse a Canonical Relationship from the generated claim, nor does it compare it against the source evidence's canonical relationship. 

## 5. Finding: Specification Ambiguity
The term "Canonical Relationship Identity" is an implicit requirement derived from the core rules ("Never attribute evidence about Drug A to Drug B"), but nowhere in the current codebase is `CanonicalRelationshipIdentity` explicitly modeled or defined as a data structure. 

## Conclusion
The audit definitively proves an **Architectural Gap**. The system enforces relationship *status*, but structurally loses the semantic *identity* of the relationship between the Normalizer and the Verifier.

## Implementation Recommendation
**ARCHITECTURAL REMEDIATION REQUIRED**
The gap cannot be closed by documentation or tests alone. A new data structure (e.g. `CanonicalRelationshipIdentity`) must be created, propagated through the `EvidenceChunk`, and evaluated structurally in `ClaimVerifierV2`.
