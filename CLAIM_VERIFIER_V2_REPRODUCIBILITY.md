# CLAIM_VERIFIER_V2_REPRODUCIBILITY

## Reproducibility Contract
The V2 semantic claim verifier depends on an offline NLI model to maintain strictly deterministic behavior across evaluations.

### Requirements:
1. **Model Freezing:** The underlying NLI model (`pritamdeka/PubMedBERT-MNLI-MedNLI`) is permanently pinned to revision `f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab`.
2. **Offline Inference:** The model is evaluated entirely offline from `cognee_service/model_cache/huggingface`. No API calls to external inference providers are permitted.
3. **Score Determinism:** For identical inputs, the pipeline must return identical `entailment`, `contradiction`, and `neutral` float values (at `fp32` precision).
4. **Scope Preservation Rules:** The `_scope_protection` deterministic rule layer is strictly versioned in `claim_verifier_v2.py`.

### Threshold Calibration Pending
Currently, the state mapping uses an `argmax` selection on the raw logits (taking the highest probability). If rigorous thresholding is required later to penalize `neutral` uncertainty, a calibration set must be isolated. Currently recorded as:
`CLAIM_VERIFIER_V2_THRESHOLD_CALIBRATION_PENDING`
