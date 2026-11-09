# CLAIM_VERIFIER_V2_STATE_MAPPING_SPEC_V1

## Overview
This specification defines the explicit, deterministic paths to reach every declared semantic support state in ClaimVerifierV2.

## 1. NLI Raw Output to State Mapping
The mapping takes max entailment, contradiction, and 
eutral across all aggregated chunks.

1. **AMBIGUOUS**:
   - Trigger: Conflicting evidence (e.g., Chunk A yields entailment > max(contradiction, 
eutral), but Chunk B yields contradiction > max(entailment, 
eutral)).
   - Trigger: The model's max entailment and contradiction scores are both high and within a margin of ambiguity (e.g., difference < 0.1, both > 0.3).

2. **CONTRADICTED**:
   - Trigger: max_contradiction > max_entailment and max_contradiction > max_neutral.

3. **SUPPORTED**:
   - Trigger: max_entailment > max_contradiction and max_entailment > max_neutral, AND the Scope/Qualification check is fully satisfied.

4. **PARTIALLY_SUPPORTED**:
   - Trigger: Used when multiple atomic clauses from the same parent sentence yield diverging states (e.g., Clause 1 is SUPPORTED, Clause 2 is UNSUPPORTED). The parent sentence conceptually maps to PARTIALLY_SUPPORTED.
   - Alternately, for an atomic claim: max_entailment is high, but the Scope check detects a minor dropping of qualifiers that reduces support but does not create an explicit contradiction or unsupported universality.

5. **UNSUPPORTED**:
   - Trigger: max_neutral is the highest score, and the claim introduces specific factual assertions (e.g., "completely safe", new entities) that go beyond the evidence. Also triggered by the Scope Protection rule when critical qualifiers (e.g., "pharmacokinetic") are dropped in favor of absolute claims.

6. **INSUFFICIENT_EVIDENCE**:
   - Trigger: max_neutral is dominant (> 0.7), and the evidence chunk provides no relevant semantic overlap to firmly judge the claim (e.g., unrelated topic, extremely short chunk).
