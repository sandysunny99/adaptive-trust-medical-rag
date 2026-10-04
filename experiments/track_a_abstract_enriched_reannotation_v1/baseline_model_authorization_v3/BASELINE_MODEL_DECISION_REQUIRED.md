# Baseline Model Decision Required

## Status
**BASELINE_AUTHORIZATION_AMBIGUOUS**

## Context
The audit has recovered a clear historical embedding model (`pritamdeka/S-PubMedBert-MS-MARCO`) that was used across all fusion evaluation experiments, but no protocol document explicitly authorizes it as the Gate 5 baseline.

## Unresolved Decisions

### 1. Should the baseline remain the deterministic SimpleEmbeddingModel?
**Evidence against**: SimpleEmbeddingModel produces 7-dimensional vectors and a zero vector for 3 of 7 Gate 5 vocabulary terms ("statin", "therapy", "cyanide", "poison", etc.). It renders the dense retrieval channel non-functional for most queries. The project architecture document (`docs/ARCHITECTURE.md`) specifies `VECTOR(768)`, which is incompatible with 7-dim output.

**Evidence for**: None found. No protocol or commit message describes SimpleEmbeddingModel as an intentional experimental baseline.

### 2. Should a real semantic model be introduced?
**Evidence for**: `pritamdeka/S-PubMedBert-MS-MARCO` was already used in 11+ experiment scripts and is recorded in two experiment manifests. `sentence-transformers>=6.0.1` is already a project dependency. The architecture specifies 768-dim embeddings.

**Evidence against**: No protocol document explicitly names this model as the authorized Gate 5 baseline.

### 3. If introducing one, what protocol defines it?
No single protocol document defines the embedding model. The closest authoritative references are:
- `docs/ARCHITECTURE.md`: specifies `VECTOR(768)` — compatible only with real transformer models
- `experiments/runs/fusion-evaluation-v3-real/manifest.json`: records `pritamdeka/S-PubMedBert-MS-MARCO`
- `experiments/runs/fusion-evaluation-v3-confirmed/manifest.json`: confirms same model

A formal protocol amendment would be required to explicitly authorize any specific model.

### 4. What version/revision is frozen?
If `pritamdeka/S-PubMedBert-MS-MARCO` is selected, its exact HuggingFace revision hash must be recorded and frozen.

### 5. How will it be provisioned offline?
The model weights must be cached locally and the cache path documented. No runtime downloads during experiment execution.

### 6. How will the change affect prior comparability?
| Prior Experiment | Embedding Used | Comparability |
|---|---|---|
| f0-f1-v2 | SimpleEmbeddingModel (DETERMINISTIC-MOCK) | NOT_COMPARABLE |
| retrieval-baseline-v1 | SimpleEmbeddingModel | NOT_COMPARABLE |
| retrieval-baseline-v2_1 | SimpleEmbeddingModel | NOT_COMPARABLE |
| fusion-evaluation-v3-real | S-PubMedBert-MS-MARCO | COMPARABLE |
| fusion-evaluation-v3-confirmed | S-PubMedBert-MS-MARCO | COMPARABLE |
| FREE_REPLICATION_V1 | SimpleEmbeddingModel (via live_variants.py) | NOT_COMPARABLE |

Switching to S-PubMedBert would make Gate 5 comparable with the fusion-evaluation experiments but NOT with the retrieval-baseline or FREE_REPLICATION experiments that used SimpleEmbeddingModel.

## Recommended Path
The strongest path is to **authorize `pritamdeka/S-PubMedBert-MS-MARCO`** as the Gate 5 dense baseline, because:
1. It is already the historically used model in the project's most rigorous retrieval experiments
2. It matches the 768-dim architecture specification
3. It is already installed via `sentence-transformers`
4. SimpleEmbeddingModel was never intended as a real baseline

However, **this decision must be made explicitly by the research lead, not by the engineering system.**

`evidence_source`: `manual_analysis`
