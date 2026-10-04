# Baseline Model Provenance Audit

## Summary
This audit traces the complete provenance of the current baseline embedding model and determines its authorization status.

## The Two Parallel Implementations

The project contains two separate embedding implementations that were never reconciled:

### Path A: `SimpleEmbeddingModel` (test fixture)
- **Introduced**: 2026-08-23, commit `ea97355`
- **Purpose at introduction**: Replace mock ablation engine with live execution pipeline
- **Vocabulary**: 7 hardcoded words
- **Vector dimension**: 7
- **Used by**: `live_variants.py`, `run_retrieval_baseline.py`, `run_baseline_v2_1.py`, orchestrator path
- **Architecture compatibility**: INCOMPATIBLE with `VECTOR(768)` in `docs/ARCHITECTURE.md`
- **Protocol authorization**: NONE. Never described as "baseline" or "authorized" in any commit or protocol document.

### Path B: `RealEmbeddingModel` with `pritamdeka/S-PubMedBert-MS-MARCO` (historical baseline)
- **Introduced**: 2026-09-11, commit `1b54194`
- **Purpose at introduction**: Real retrieval evaluation with biomedical semantic embeddings
- **Vector dimension**: 768
- **Used by**: 11+ experiment scripts (`run_fusion_evaluation.py`, `run_cross_encoder_fusion.py`, etc.)
- **Recorded in experiment manifests**: `fusion-evaluation-v3-real/manifest.json`, `fusion-evaluation-v3-confirmed/manifest.json`
- **Architecture compatibility**: COMPATIBLE with `VECTOR(768)` in `docs/ARCHITECTURE.md`
- **Protocol authorization**: IMPLICIT (used in experiments but not explicitly named in any protocol document)

## How SimpleEmbeddingModel Entered the Architecture Snapshot

1. `SimpleEmbeddingModel` was created in `live_variants.py` as a testing mock (Aug 23)
2. The orchestrator baseline path imports from `live_variants.py`, inheriting the mock
3. When `CURRENT_ARCHITECTURE_SNAPSHOT.md` was created (Sep 13, commit `b18461d`), it simply described the current code state
4. The snapshot recorded "Dense (SimpleEmbeddingModel)" because that was what the code used — not because the protocol intended it

## Why This Was Never Caught

The experiment scripts in `scripts/` define their own `RealEmbeddingModel` class locally and bypass the orchestrator's embedding path entirely. The orchestrator integration tests used `SimpleEmbeddingModel` because it was convenient and deterministic. The two paths never intersected in a way that would expose the mismatch.

## Dependency Evidence

`pyproject.toml` declares `sentence-transformers>=6.0.1` (Phase 10 dependency). This was added to support the experiment scripts, not the orchestrator baseline. The dependency is installed but not imported by the orchestrator retrieval path.

## Conclusion

`SimpleEmbeddingModel` is a **test fixture that was accidentally promoted into the architecture snapshot**. The historically used semantic baseline is `pritamdeka/S-PubMedBert-MS-MARCO`, but its authorization for Gate 5 specifically is implicit rather than explicit.

`evidence_source`: `manual_analysis`
