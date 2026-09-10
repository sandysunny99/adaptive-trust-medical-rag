# Phase 2E Metric Provenance Map

### 1. Recall@5
- **Raw Input**: `case_results.jsonl`
- **Calculation**: Count cases with `first_relevant_rank <= 5`
- **Denominator**: Total positive cases
- **Script**: `scripts/metrics_f3.py`, `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified

### 2. MRR
- **Raw Input**: `case_results.jsonl`
- **Calculation**: `1 / first_relevant_rank` if `<= 5`, else `0`
- **Denominator**: Total positive cases
- **Script**: `scripts/metrics_f3.py`, `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified

### 3. Domain Metrics (DDI, ADE, Safety, High-Risk)
- **Raw Input**: `case_results.jsonl`, `retrieval_dataset_v2_1.json`
- **Calculation**: Compute `Recall@5` strictly for cases where `claim_type` or `risk_tier` matches the domain.
- **Denominator**: Total positive cases within that domain
- **Script**: `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified

### 4. Hard-Negative Rank
- **Raw Input**: `case_results.jsonl`
- **Calculation**: Identify rank of noise document `42062777` (monitoring) in F0 vs F3 candidate arrays. Asserts relevance is `False`.
- **Denominator**: Single case `e-12`
- **Script**: `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified

### 5. Entity Precision (Top-1 Correct Entity Rate)
- **Raw Input**: `case_results.jsonl`, `documents.json`, `retrieval_dataset_v2_1.json`
- **Calculation**: Check if text of Rank-1 document contains the raw strings of `expected_entity_ids`.
- **Denominator**: Total positive cases
- **Script**: `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified

### 6. Authority Coverage (Relevant Authoritative Top-5 Rate)
- **Raw Input**: `case_results.jsonl`, `documents.json`
- **Calculation**: Count cases where *at least one* document in Top-5 is BOTH in `expected_document_ids` AND has `provider` in `{"FDA", "PubMed_Central", "pubmed"}`.
- **Denominator**: Cases that have an authoritative expected document
- **Script**: `scripts/verify_phase2e_metrics.py`
- **Verification Status**: Verified