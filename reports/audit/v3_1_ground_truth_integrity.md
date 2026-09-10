# V3.1 Ground Truth Integrity Report

| Check | Status | Note |
| :--- | :--- | :--- |
| Corpus Exists | **PASS** | Corpus is permanently frozen at `corpus_sha256`: `cd7491f687d290a384e9d03b3868a725b14f528ee2a06a32718c5593609ad1e2`. |
| All Document IDs Exist | **PASS** | Evaluated positive cases trace to frozen corpus. |
| Evidence Spans Exist | **PASS** | Extracted via deterministic heuristic. |
| Evidence Hashes Match | **PASS** | SHA256 matches precisely. |
| No Model Scores in GT | **PASS** | Word overlap scores were used for generation but not persisted in the final `retrieval_ground_truth_v3_1_manual.json`. |
| No Retrieval Ranks in GT | **PASS** | F0/F3 ranks were strictly excluded. |
| Query/Corpus Separation | **PASS** | 0% exact match leakage, 0 high token-overlap leakage verified. |
| No Synthetic Documents | **PASS** | Corpus consists entirely of 248 real PubMed abstracts. |
| No Templated Clone Cases | **PASS** | Queries authored independently. |
| No Retrieval-derived Hard Negatives | **PASS** | Hard negatives derived from word overlap / entity mismatch, not F0 retrieval failure. |
| Corpus Hash Stable | **PASS** | Frozen prior to evaluation. |
| Ground-Truth Hash Stable | **PASS** | Frozen prior to evaluation. |
| **Ground-Truth Independence** | **FAIL** | **Ground truth was generated using automated lexical/heuristic rules (word overlap / entity co-occurrence) without independent human review.** |

## Conclusion
**OVERALL INTEGRITY: FAIL**

Because Ground-Truth Independence FAILED, this dataset must be classified as `AUTOMATED_DIAGNOSTIC_ONLY`. It cannot be used as final model-selection evidence for V3.1 Confirmation.