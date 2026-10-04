# CLAIM_VERIFIER_V2_REPRODUCIBILITY_V2

## Reproducibility Verification
The complete semantic V2 component suite (16 tests) was executed multiple times, confirming absolute determinism across all runs.

### Verified Consistency Dimensions:
1. **Atomic Claim Decomposition:** The deterministic `clause_re` consistently and symmetrically isolated clauses separated by `and therefore`, `and`, `but` in multi-proposition sentences.
2. **Selected Evidence IDs:** The evidence aggregation strictly tracked the highest NLI parameters (`max_entailment`, `max_contradiction`, `max_neutral`) and accurately surfaced the `best_chunk` references without variance.
3. **NLI Output:** Using the frozen offline `safetensors` model (`PubMedBERT-MNLI-MedNLI`), repeated inference passes over the identical strings yielded the exact same floating-point logits.
4. **Final Support State:** The `_determine_state` mapping logic paired with the decoupled `_scope_protection` layer yielded invariant semantic states across runs.
5. **Citation State:** The `CitationValidation` object decoupled semantic support from mere syntax, correctly rejecting citation-supported claims that lacked actual semantic grounding.
6. **Gate Decision:** The final `GateDecision.release` / `abstain` boundaries held firm.

### Threshold Status
Explicitly maintained as `THRESHOLD_CALIBRATION_STATUS = PENDING`. The decision currently routes via deterministically bounded `argmax` mapping (with explicit scope safety overrides), documented as the intended prototype configuration. No silent probability calibration shifts occurred.
