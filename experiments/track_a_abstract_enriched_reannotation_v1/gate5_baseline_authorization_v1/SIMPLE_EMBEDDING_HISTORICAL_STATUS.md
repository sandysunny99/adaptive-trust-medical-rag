# SimpleEmbeddingModel Historical Methodological Status

## Thesis Record: Preservation of Methodological History

This document explicitly preserves the research provenance of the dense retrieval baseline resolution, explaining why earlier retrieval experiments must not be silently combined with new Gate 5 results.

The methodological sequence was as follows:

1. **Introduction of Engineering Fixture:** `SimpleEmbeddingModel` was introduced on August 23 (commit `ea97355`) purely as a 7-word deterministic testing fixture to replace a mock ablation engine. It output 7-dimensional vectors.
2. **Incorrect Architectural Capture:** Because it was imported by the default `live_variants.py` execution path, it was inadvertently captured by the `CURRENT_ARCHITECTURE_SNAPSHOT.md` script on September 13.
3. **Misleading Baseline Retrieval:** This resulted in misleading retrieval behavior (zero-vectors for critical queries like "statin therapy is common") that artificially deflated the apparent dense retrieval recall.
4. **Historical Semantic Baseline Recovery:** A provenance audit discovered that the project's actual rigorous retrieval evaluation (`fusion-evaluation-v3`) utilized `pritamdeka/S-PubMedBert-MS-MARCO` (a 768-dimensional model) across 11+ scripts, aligning perfectly with the underlying database specification of `VECTOR(768)`.
5. **Formal Gate 5 Protocol Amendment:** To resolve the discrepancy between the default orchestrator path and the historical experimental intent, a formal protocol amendment was issued to explicitly adopt and freeze the `S-PubMedBert` model.

By preserving this history, we ensure that prior experiments (such as `FREE_REPLICATION_V1` and `retrieval-baseline-v1`) that relied on the test fixture are recognized as structurally incomparable to the true Gate 5 dense evaluation, protecting the scientific integrity of the experimental timeline.

`evidence_source`: `manual_analysis`
