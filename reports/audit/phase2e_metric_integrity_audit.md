# Phase 2E Metric Integrity Audit

| Metric | Source | Computed? | Hard-coded? | Supported? | Action Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Recall@5 | `case_results.jsonl` | Yes | No | Yes | None |
| MRR | `case_results.jsonl` | Yes | No | Yes | None |
| Domain Metrics (DDI, ADE, Safety) | `case_results.jsonl` | Yes | No | Yes | Add sample sizes (n) |
| Hard-Negative Rank (e-12) | `case_results.jsonl` | No (Previously) | Yes (Previously) | No | Recompute from candidate pool comparing document ID `42062777` |
| Entity Precision Maintained | N/A | No (Previously) | Yes (Previously) | No | Delete hard-coded assertion. Compute actual entity overlap |
| Authoritative Coverage Preserved | N/A | No (Previously) | Yes (Previously) | No | Delete hard-coded assertion. Compute from document provider/tier |
| Difficulty Metrics | `case_results.jsonl` | Yes | No | Yes | Ensure expected_documents count > 0 |

**Status**: ALL previously hard-coded assertions have been removed and replaced with empirical code parsing raw evaluation data.