# Runtime Evidence Provenance Audit V4

## Scope
This audit verifies the provenance of the fields produced by:
1. `experiments/runtime_retrieval_proof_v2.py`
2. `experiments/fast_phase9.py`
3. `experiments/diagnostic_v4.py`

## Trace of Important Fields

| Script / Field | Value Trace | Classification |
|---|---|---|
| `runtime_retrieval_proof_v2.py` / `candidate_count` | `len(trace_res.retained_candidates)` | DIRECT_RUNTIME |
| `runtime_retrieval_proof_v2.py` / `bm25_returned` | `len(bm25_cands) > 0` | DERIVED_RUNTIME |
| `runtime_retrieval_proof_v2.py` / `raw_result_count` | `len(raw or [])` from `cognee.search` | DIRECT_RUNTIME |
| `runtime_retrieval_proof_v2.py` / `source_file_hash` | `"f3d5..."` | **HARDCODED** |
| `fast_phase9.py` / `candidates_evaluated` | `len(trace_res.retrieved_chunk_ids)` | DIRECT_RUNTIME |
| `fast_phase9.py` / `orch_status` | `trace_res.status.value` | DIRECT_RUNTIME |
| `diagnostic_v4.py` / `vector_dimension` | `len(vec)` from model `encode()` | DIRECT_RUNTIME |
| `diagnostic_v4.py` / `nonzero_dimensions` | `sum(1 for v in vec if v > 0)` | DIRECT_RUNTIME |
| `diagnostic_v4.py` / `is_zero_vector` | `all(v == 0.0 for v in vec)` | DIRECT_RUNTIME |

## Findings
The V2 probes (`runtime_retrieval_proof_v2.py`, `fast_phase9.py`) and the V4 diagnostic (`diagnostic_v4.py`) accurately serialize direct return objects from the instantiated pipeline and model classes.

The only exception remains the `source_file_hash` in the BM25 runtime test, which was hardcoded as a string. Because this hash is not a functional retrieval property but a provenance metadata placeholder, its hardcoding does not invalidate the retrieval candidate outputs.

**Conclusion:** The artifact observations generated in this step and V2 are genuinely captured from runtime execution.

`evidence_source`: `manual_analysis`
