# Gate 5 Baseline Comparability Matrix

## Protocol Change Impact
This document explicitly records that the new Gate 5 baseline protocol amendment fundamentally alters the semantic retrieval channel relative to some prior experiments. 

Because `SimpleEmbeddingModel` (a 7-dim test fixture) was inadvertently used in early default orchestrator executions, historical results are permanently bifurcated.

**No historical result is rewritten or relabeled.** Future Gate 5 results will use the new frozen `S-PubMedBert-MS-MARCO` baseline, and prior results using `SimpleEmbeddingModel` will remain historical artifacts with disclosed comparability limitations.

## Comparability Matrix

| Prior Experiment | Status | Reason |
|---|---|---|
| `fusion-evaluation-v3-real` | **FULLY_COMPARABLE** | This experiment explicitly configured and used `S-PubMedBert-MS-MARCO` to generate candidates before fusion, identical to the new baseline. |
| `fusion-evaluation-v3-confirmed` | **FULLY_COMPARABLE** | Same as above. |
| `retrieval-baseline-v1` | **NOT_COMPARABLE** | Used `SimpleEmbeddingModel`. The dense retrieval channel behavior was fundamentally different (zero vectors for most queries). |
| `retrieval-baseline-v2_1` | **NOT_COMPARABLE** | Used `SimpleEmbeddingModel`. |
| `f0-f1-v2` | **NOT_COMPARABLE** | Experiment ran in `DETERMINISTIC-MOCK` mode using `SimpleEmbeddingModel`. |
| `FREE_REPLICATION_V1` | **NOT_COMPARABLE** | Inherited the orchestrator's default `SimpleEmbeddingModel` constraint. Any direct mathematical comparison to the new Gate 5 dense retrieval performance is invalid. |

`evidence_source`: `manual_analysis`
