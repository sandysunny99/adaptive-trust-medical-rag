# API Reproducibility & Frozen Snapshot Audit Report

**Status:** `AUDITED & REPRODUCIBLE`  
**Timestamp:** 2026-08-23T18:22:00Z  

---

## 1. Research Reproducibility Architecture

To prevent live API response drift from compromising benchmark evaluations, all evidence source adapters support two execution modes:

```text
       ┌────────────────────────┐
       │ EvidenceSourceAdapter │
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
  LIVE_API_MODE    FROZEN_SNAPSHOT_MODE
  (Development)    (Research Benchmark)
         │                   │
  Live HTTP Fetch    Replay Verified JSON Snapshot
         │                   │
         └─────────┬─────────┘
                   ▼
         Deterministic Hashing (SHA-256)
                   ▼
         Identical Evidence Indices
```

---

## 2. Snapshot Manifest (`experiments/manifests/external_sources_v1.json`)

The frozen snapshot manifest stores pre-downloaded, SHA-256 verified API response payloads:

- **Manifest Path:** `experiments/manifests/external_sources_v1.json`
- **Recorded Providers:** NCBI PubMed, Europe PMC, NLM RxNorm, openFDA
- **Verification Rule:** `indep_hash == recorded_response_hash` must equal `PASS` for all 100% replay integrity.
