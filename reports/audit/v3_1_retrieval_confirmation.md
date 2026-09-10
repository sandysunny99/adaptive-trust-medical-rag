# V3.1 Retrieval Confirmation Report

## 1. Configurations
- **F0**: `BM25 + S-PubMedBERT + Graph -> RRF(k=60) -> Top-20`
- **F3**: `F0 Top-20 -> ncbi/MedCPT-Cross-Encoder -> reranked Top-20`

## 2. Integrity Audit Results
- **Ground-Truth Independence**: **FAIL**
- **Benchmark Status**: `AUTOMATED_DIAGNOSTIC_ONLY`
- The labels were derived automatically using word overlap and entity co-occurrence, lacking genuine independent human clinical review. Therefore, this benchmark cannot act as final confirmation.

## 3. Evaluation Proxy Metrics (n=59 positives)
| Metric | F0 (RRF Baseline) | F3 (MedCPT) |
| :--- | :--- | :--- |
| **Recall@5** | 0.932 | 0.932 |
| **MRR@20** | 0.782 | 0.729 |
| **Candidate-Pool Recall@20** | 1.000 | 1.000 |

*Note: The differences are not statistically significant (p = 0.139). MedCPT does not mathematically regress performance on this dataset, but the dataset itself is invalid for final confirmation.*

## 4. Scientific Claim
**MedCPT improved the observed ranking inversions in earlier diagnostic experiments and is a promising candidate for biomedical reranking. Its superiority has not yet been confirmed on an independently annotated real-evidence benchmark.**

## 5. Decision
**F3_INCONCLUSIVE** (pending true human annotation)

## 6. Project Status
Because true independent relevance labels could not be obtained programmatically, I have enforced the **Immediate Stop Rule**.

Phase 2G (Controlled Integration) remains **BLOCKED** until V3.1 passes the integrity gate via human-annotated ground truth.