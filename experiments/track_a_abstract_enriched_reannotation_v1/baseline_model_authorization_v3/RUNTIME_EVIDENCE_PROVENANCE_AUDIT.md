# Runtime Evidence Provenance Audit

## Scope
This audit examines the evidence provenance of artifacts produced by:
1. `generate_repair_artifacts.py` (V1 — INVALIDATED)
2. `experiments/runtime_retrieval_proof_v2.py` (V2)
3. `experiments/fast_phase9.py` (V2)

## Phase 1 — V1 Artifacts (generate_repair_artifacts.py)

**STATUS: INVALIDATED — EVIDENCE_NOT_RUNTIME_DERIVED**

Every field in the V1 artifacts was programmatically hardcoded by the generation script. No value was extracted from a live runtime execution. Specifically:

| Artifact | Evidence Source | Classification |
|---|---|---|
| `BM25_REPAIR_REPORT.md` | Manually authored narrative | C: manually_authored |
| `BM25_REGRESSION_RESULTS.json` | Hardcoded `"score": 1.3862...` | D: programmatically_hardcoded |
| `BASELINE_EMBEDDING_MODEL_AUDIT.md` | Manually authored narrative | C: manually_authored |
| `BASELINE_EMBEDDING_STATUS.json` | Hardcoded `"status": "BASELINE_EMBEDDING_UNSPECIFIED"` | D: programmatically_hardcoded |
| `COGNEE_GATE5_QUERY_PROOF.jsonl` | Hardcoded `"candidate_count": 4` | F: expected_outcome |
| `BASELINE_GATE5_QUERY_PROOF.jsonl` | Hardcoded `"bm25_result_count": 4` | F: expected_outcome |
| `RRF_DIAGNOSTIC.json` | Manually authored conclusion | C: manually_authored |
| `RETRIEVAL_TO_SECURITY_TRACE.jsonl` | Hardcoded `"decision": "PROCEED"` | F: expected_outcome |
| `RETRIEVAL_PRIMITIVE_STATUS.json` | Hardcoded status | D: programmatically_hardcoded |
| `RETRIEVAL_PRIMITIVE_REPAIR_FINAL.md` | Manually authored narrative | C: manually_authored |

**NONE of these artifacts contain genuine runtime evidence. They must not be cited as experimental proof.**

## Phase 2 — V2 Artifacts (runtime_retrieval_proof_v2.py)

The V2 script was architecturally correct: it instantiates live objects and serializes their return values. However:

| Field | Source of Value | Classification |
|---|---|---|
| `BM25_REAL_RUNTIME_TEST.json` — `scores` | Direct return from `BM25Retriever.retrieve()` | A: direct_live_return_object |
| `BM25_REAL_RUNTIME_TEST.json` — `source_file_hash` | Hardcoded string `"f3d5..."` | D: programmatically_hardcoded |
| `COGNEE_GATE5_QUERY_PROOF.jsonl` — `raw_result_count` | `len(raw or [])` from `cognee.search()` | A: direct_live_return_object |
| `COGNEE_GATE5_QUERY_PROOF.jsonl` — `candidate_text` | `r.get("text")` from Cognee search result | A: direct_live_return_object |
| `BASELINE_GATE5_QUERY_PROOF.jsonl` — `bm25_results` | Direct return from `hybrid.bm25.retrieve()` | A: direct_live_return_object |
| `BASELINE_GATE5_QUERY_PROOF.jsonl` — `dense_results` | Direct return from `hybrid.vector.retrieve()` | A: direct_live_return_object |
| `RRF_DIAGNOSTIC.jsonl` — `bm25_returned` | `len(bm25_cands) > 0` | B: derived_from_live_return |

## Phase 3 — V2 Security Trace (fast_phase9.py)

| Field | Source of Value | Classification |
|---|---|---|
| `candidates_evaluated` | `len(trace_res.retrieved_chunk_ids)` from `orch.query()` | A: direct_live_return_object |
| `orch_status` | `trace_res.status.value` from `orch.query()` | A: direct_live_return_object |

**The V2 artifacts are genuinely runtime-captured except for the `source_file_hash` field, which was hardcoded as a placeholder.**

## Recommendation

- V1 artifacts: **DISCARD as evidence. Keep only as historical record of what was generated.**
- V2 artifacts: **Usable as runtime evidence with the caveat that `source_file_hash` needs recalculation.**

`evidence_source`: `manual_analysis`
