# FULL GATE 5 EVIDENCE AUDIT: EXECUTION PATH VERIFICATION

> **Status: FULL_EXECUTION_PATH_FAILED_WITH_LIMITATIONS**
> **Gate 5: FAILED_WITH_LIMITATIONS (unchanged)**
> **Gate 6: NOT AUTHORIZED / STOPPED**

---

## 1. Exact Script Execution Architecture

The script [`cognee_gate5_full_rerun.py`](file:///c:/Users/sunny/Downloads/CASE%20STUDY/experiments/cognee_gate5_full_rerun.py) (465 lines) uses a **three-phase architecture**:

```
Phase 1: COGNEE INGESTION (lines 85-118)
  cognee.prune.prune_data()
  cognee.prune.prune_system()
  cognee.add(data_items, dataset_name="gate5_dataset")
  cognee.cognify()                    ← CALLED, BUT FAILED TO BUILD GRAPH

Phase 2: PRECOMPUTED SEARCH BATCH (lines 368-375)
  for each of 23 cases:
    try:
      precomputed[query] = await cognee.search(query, CHUNKS, datasets=["gate5_dataset"])
    except Exception:                 ← SILENTLY CATCHES NoDataError
      precomputed[query] = []         ← REPLACES WITH EMPTY LIST

Phase 3: CASE EXECUTION (lines 377-385)
  ThreadPoolExecutor:
    for case x mode x run:
      run_case(case, run_idx, mode, manifest, registry, precomputed)
```

> [!CAUTION]
> `BridgedCogneeAdapter.retrieve()` (line 145) does **`results = self.precomputed_search.get(query, [])`**. It **never** calls `cognee.search()` at case execution time. The Cognee retrieval step is entirely a dict lookup against the precomputed cache.

---

## 2. Exact Cognee Call Path

```
main()
  └─ ingest_cognee()
       ├─ cognee.prune.prune_data()        ✓ executed
       ├─ cognee.prune.prune_system()       ✓ executed
       ├─ cognee.add(6 DataItems)           ✓ executed
       └─ cognee.cognify()                  ✓ called, ✗ FAILED (empty graph)
  └─ Precompute loop (lines 368-375)
       ├─ cognee.search("statin therapy...")          → NoDataError → []
       ├─ cognee.search("Does statin interact...")    → NoDataError → []
       ├─ cognee.search("Statin is a drug...")        → NoDataError → []
       ├─ cognee.search("statin")                     → NoDataError → []
       ├─ cognee.search("statin interacts with...")    → NoDataError → []
       ├─ cognee.search("Statin therapy is common...") → NoDataError → []
       ├─ cognee.search("Does statin interact with ibuprofen?") → NoDataError → []
       └─ cognee.search("Does metformin interact...")  → NoDataError → []
  └─ ThreadPoolExecutor (92 cases)
       └─ BridgedCogneeAdapter.retrieve(query)
            └─ self.precomputed_search.get(query, [])  → always []
```

> [!IMPORTANT]
> The NoDataError message from Cognee was: *"No searchable memory in dataset 'gate5_dataset' (id: e66674eb-...): holds 6 data item(s) but its knowledge graph is empty; run cognify on this dataset before searching."*
> 
> `cognify()` was called. It did not produce a searchable state.

---

## 3. Whether Live Cognee Ran Per Case

**No.** Zero live Cognee searches occurred at case execution time.

- `cognee.search()` was called **8 times** (for 8 unique query strings) during the precompute batch in `main()`.
- All 8 calls raised `NoDataError`.
- All 8 results were silently replaced with `[]`.
- The remaining 15 cases shared query strings with the first 8, so their precomputed results were reused from the dict.
- At case execution time, `BridgedCogneeAdapter.retrieve()` performed only `self.precomputed_search.get(query, [])`.

---

## 4. Counts

| Category | Count |
|----------|-------|
| Live Cognee searches (precompute phase) | 8 (unique queries) |
| Cognee searches returning results | **0** |
| Cognee searches raising NoDataError | **8** |
| Precomputed results reused (shared queries) | 15 |
| Live Cognee searches at case execution time | **0** |
| NoDataError / empty graph cases | **23 (all)** |

---

## 5. Baseline Execution Accounting

| Metric | Value |
|--------|-------|
| Records | 46 (23 cases × 2 runs) |
| Retrieval adapter | `BaseAdapterMock` (deterministic manifest iteration) |
| Candidates returned | 1 per case (filtered to target doc_id) |
| Live external search | None (synthetic mock) |
| Security controls exercised | Yes (integrity, grounding, poisoning, injection) |

---

## 6. Cognee Execution Accounting

| Metric | Value |
|--------|-------|
| Records | 46 (23 cases × 2 runs) |
| Retrieval adapter | `BridgedCogneeAdapter` (precomputed cache lookup) |
| Candidates returned | **0 for all 46 records** |
| Live Cognee search at retrieval | **None** |
| Security controls exercised on Cognee candidates | **None** |
| Identity bridge exercised | **No** (no candidates to bridge) |
| Tamper scenarios exercised | **No** (TamperingRetrievalWrapper received empty lists) |

---

## 7. Cognee Execution Path Classification (All 23 Cases)

All 23 cases: **`E_FALLBACK_EMPTY_GRAPH`**

```
LIVE_NATIVE_COGNEE:       0
LIVE_COGNEE_WITH_ADAPTER: 0
PRECOMPUTED_COGNEE_RESULT: 0 (precompute occurred but returned nothing)
CACHED_RESULT:            0
FALLBACK_EMPTY_GRAPH:     23  ← ALL CASES
HYBRID_SUBSTITUTION:      0
OTHER:                    0
```

---

## 8. 92 Record Accounting

```
BASELINE:  23 × 2 = 46  (MOCK_ADAPTER)
COGNEE:    23 × 2 = 46  (PRECOMPUTED_EMPTY_CACHE)
TOTAL:               92  ✓ reconciled
```

---

## 9. Positive Control Status

| Case | Baseline | Cognee |
|------|----------|--------|
| POS-01 | RELEASE ✓ | BLOCK (0 candidates) ✗ |
| POS-02 | RELEASE ✓ | BLOCK (0 candidates) ✗ |

**COGNEE_POSITIVE_CONTROL = NOT_EXECUTED_SUCCESSFULLY**

---

## 10. RG-02 Status

| Path | Retrieved? | Grounding | Alignment | Eligibility | Cause |
|------|-----------|-----------|-----------|-------------|-------|
| Baseline | Yes (doc_rg02) | UNVERIFIABLE | MISMATCH | BLOCK | INTEGRITY_MISSING_REFERENCE |
| Cognee | No (0 candidates) | NOT_EXECUTED | NOT_EXECUTED | BLOCK | ZERO_CANDIDATES |

RG-02 invariant (`aligned_supporting == 0 → BLOCK`) is **satisfied on Baseline**. On Cognee, the BLOCK was caused by empty retrieval, not by grounding evaluation.

---

## 11. Reproducibility Classification

| Path | Type | Interpretation |
|------|------|---------------|
| Baseline | DETERMINISTIC_MOCK_REPEATED | Same synthetic adapter produced identical results. Expected. Not informative about production stability. |
| Cognee | SAME_FAILURE_REPEATED | Same empty-cache lookup repeated. "DECISION_EXACT_MATCH: true" means both runs produced the same 0-candidate BLOCK. |

The 100% reproducibility figure is **arithmetically correct but experimentally vacuous** for the Cognee path.

---

## 12. Protocol Conformance Matrix

| Req | Description | Status | Evidence |
|-----|-------------|--------|----------|
| A | All authorized cases executed | ✅ PASS | 92 records |
| B | Both retrieval modes actually executed | ❌ FAIL | Cognee invoked but returned nothing |
| C | Positive controls successfully exercised | ❌ FAIL | RELEASE only on Baseline |
| D | Security threats actually exercised | ❌ FAIL | Only on Baseline candidates |
| E | RG-02 exercised through actual retrieval | ❌ FAIL | Only on Baseline |
| F | Cognee trusted evidence crossed bridge | ❌ FAIL | Bridge code never executed with data |
| G | Expected vs observed comparison | ⚠️ CAVEAT | Implemented but POS-02 Cognee was never achievable |
| H | No step replaced by cached behavior | ❌ FAIL | Precomputed cache substitution |
| I | Artifact validation independently passed | ✅ PASS | scratch_validation.py confirmed |
| J | Reproducibility contract satisfied | ❌ FAIL | Same-failure-repeated, not retrieval reproducibility |

**Failed requirements: 7 of 10. Passed: 2. Caveat: 1.**

---

## 13. Deviations Found

1. `cognee.cognify()` ran but did not produce a searchable vector/graph state.
2. All `cognee.search()` calls raised `NoDataError`, silently caught and replaced with `[]`.
3. `BridgedCogneeAdapter` used precomputed cache (dict lookup), not live per-case `cognee.search()`.
4. `TamperingRetrievalWrapper` received 0 candidates on all Cognee runs; no tamper scenario was exercised on Cognee.
5. Positive controls (POS-01, POS-02) achieved BLOCK on Cognee due to 0 candidates, not RELEASE.
6. RG-02 was not exercised through Cognee retrieval.
7. The `BridgedCogneeAdapter` identity/provenance bridge code was never executed with real Cognee data.
8. Reproducibility for Cognee records measures cache consistency of empty results, not retrieval consistency.

---

## 14. Final Status

| Item | Status |
|------|--------|
| Gate 5 | **FULL_GATE5_FAILED_WITH_LIMITATIONS** (unchanged) |
| Gate 6 | **NOT AUTHORIZED / STOPPED** |
| Execution path | **FULL_EXECUTION_PATH_FAILED_WITH_LIMITATIONS** |
| New Full Gate 5 execution required | **YES** |

---

## 15. What the Run Does Establish

- The orchestrator does not crash when retrieval returns 0 candidates (fail-closed to BLOCK).
- Baseline mock retrieval correctly exercises security controls (grounding, integrity, poisoning, injection).
- RG-02 invariant (`aligned_supporting_candidate_count == 0 → BLOCK`) holds on Baseline.
- Artifact generation and hashing pipeline works correctly.
- 1,033 regression tests pass independently.

## 16. What the Run Does NOT Establish

- Successful Cognee retrieval for any case.
- Cognee candidate evaluation through the trust/provenance/grounding pipeline.
- Cognee identity bridge functioning with real search results.
- Positive control RELEASE through the Cognee path.
- Security threat exercise against Cognee-retrieved candidates.

## 17. Prerequisites for Next Full Gate 5

Before a new Gate 5 execution:

1. **Resolve `cognify()` failure**: Determine why `cognee.cognify()` does not build a searchable graph from the 6 ingested DataItems.
2. **Remove precomputed cache architecture**: Replace the precompute-then-lookup pattern with live `cognee.search()` at case retrieval time.
3. **Verify Cognee search returns candidates**: Confirm at least POS-01 and POS-02 queries return non-empty results before running the full matrix.
4. **Remove silent exception swallowing**: Replace `except Exception: precomputed[...] = []` with explicit error logging and case-level failure recording.

---

*Audit produced by independent source-code and artifact inspection. No files modified. No logic changed.*
