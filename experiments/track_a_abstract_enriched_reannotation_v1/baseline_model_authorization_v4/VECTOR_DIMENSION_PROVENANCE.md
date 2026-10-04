# VECTOR(768) Provenance

## Origin
The `VECTOR(768)` specification was introduced to the project database schema in `docs/ARCHITECTURE.md`.

*   **Commit:** `b6d9dd149acc699897ca1ad0c8869a0e2e9b9a69`
*   **Date:** 2026-08-23 11:43:37 +0530
*   **Author:** sandysunny99
*   **Purpose:** "Phase 24 - Comprehensive System Documentation & Production Readme / Research Paper Artifacts"

## Analysis

The 768-dimension specification was introduced on **Aug 23**. This is significant because:
1.  It predates the introduction of `S-PubMedBert-MS-MARCO` (introduced Sep 11).
2.  It was committed just hours before `SimpleEmbeddingModel` (a 7-dimensional mock) was introduced in commit `ea97355` (Aug 23 14:20:01).

## Conclusion
The `VECTOR(768)` dimension was likely chosen because 768 is the standard dimension for BERT-base architecture embeddings (including standard `sentence-transformers`, `SBERT`, and `PubMedBERT`).

**Crucially:** 768 was NOT chosen specifically because `S-PubMedBert-MS-MARCO` was the authorized model. Rather, 768 was chosen as a standard placeholder dimension for *any* future BERT-based semantic model. Therefore, while `S-PubMedBert` matches this dimension, the dimension itself does not constitute formal authorization for that specific model over another 768-dim model.

`evidence_source`: `manual_analysis`
