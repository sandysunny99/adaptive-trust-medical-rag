# Gate 5 Baseline Authorization and Model Freeze Final Report

## Final Status
**`BASELINE_AUTHORIZED_AND_FROZEN`**

## Summary
The research lead formally authorized `pritamdeka/S-PubMedBert-MS-MARCO` as the official Gate 5 dense retrieval baseline via `GATE5_BASELINE_MODEL_PROTOCOL_AMENDMENT_V1.md`.

This decision replaces the `SimpleEmbeddingModel` (a 7-dim test fixture) with the project's historical biomedical semantic model, aligning the orchestrator retrieval path with the `VECTOR(768)` database specification and restoring comparability with the `fusion-evaluation-v3` experimental results.

## Freeze Validation Checklist
- **Model ID Confirmed:** `pritamdeka/S-PubMedBert-MS-MARCO`
- **Exact Revision Confirmed:** `96786c7024f95c5aac7f2b9a18086c7b97b23036`
- **Configuration Confirmed:** `GATE5_BASELINE_CONFIG_V1.json` (768-dim, mean pooling, L2 normalization)
- **Offline Provisioning Confirmed:** Model is locally cached in `.cache/huggingface/hub/models--pritamdeka--S-PubMedBert-MS-MARCO` (`SPUBMEDBERT_OFFLINE_PROVISIONING_MANIFEST.json`)
- **Dimension Verified:** Runtime verification successfully confirmed exactly 768 dimensions (`SPUBMEDBERT_RUNTIME_VERIFICATION.json`)
- **Runtime Embedding Verified:** Runtime outputs non-zero vectors for Gate 5 queries.
- **Baseline Retrieval Verified:** The semantic path (`vector.retrieve()`) generated genuine candidates without exceptions (`SPUBMEDBERT_DENSE_RETRIEVAL_PROOF.jsonl`).
- **Security Boundary Traversal:** A genuine candidate was successfully queried via the `AdaptiveTrustRAGOrchestrator`, resulting in a recorded security status trace (`SECURITY_TRACE_V1.jsonl`).

## Next Steps
The protocol is now fully amended and the baseline implementation is frozen and verified.

The immediate next milestone is to verify a final small readiness test using POS-01, POS-02, and RG-02 traversing both the live Cognee path and the real frozen S-PubMedBert baseline, checking identity, provenance, trust, and eligibility through the full security boundary.

*Note: The 23-case Gate 5 matrix must not be executed until this final readiness validation is complete.*

`evidence_source`: `manual_analysis`
