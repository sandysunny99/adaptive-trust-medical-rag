# CLAIM_VERIFIER_V2_EVIDENCE_AGGREGATION_SPEC_V1

## Overview
Defines the deterministic aggregation policy for evaluating a claim against multiple evidence chunks.

## Aggregation Rule
For each atomic claim, the verifier must evaluate **ALL** eligible evidence chunks (either all cited chunks, or all retrieved chunks if no citation exists).

Instead of greedily retaining only the chunk with the highest entailment, the verifier independently tracks:
- max_entailment (and its corresponding est_entailment_chunk_id)
- max_contradiction (and its corresponding est_contradiction_chunk_id)
- max_neutral (and its corresponding est_neutral_chunk_id)

## Decision Priority
1. **Conflict Check**: If one chunk yields highest entailment and a *different* chunk yields highest contradiction (and both are dominant in their respective runs), this indicates **Conflicting Evidence** (maps to AMBIGUOUS).
2. **Contradiction Independence**: A strong contradiction (max_contradiction > threshold/argmax) from *any* chunk overrides a weak entailment from another chunk.
