# Phase 2E: Biomedical Reranker Evaluation (V3) - Corrected

## 1. Experimental Objective
Evaluate whether a cross-encoder specifically trained on biomedical semantic relationships (`ncbi/MedCPT-Cross-Encoder`) could successfully recognize and promote the relevant clinical evidence that naive RRF (F0) demoted.

## 2. V2.1 Benchmark Limitations
This experiment is conducted on the V2.1 Diagnostic Benchmark, which contains exactly 6 positive cases. All metrics below are explicitly annotated with sample size (n) to reflect this diagnostic scope.

## 3. F0 Configuration
- **Primary Encoder**: `E1` (`pritamdeka/S-PubMedBert-MS-MARCO`)
- **Fusion Control**: `F0` (Current RRF, k=60, equal weights)
- **Candidate Pool Size**: N = 20

## 4. MedCPT Configuration
- **Biomedical Reranker**: `F3` (`ncbi/MedCPT-Cross-Encoder`)

## 5. Candidate-Pool Recall
Before evaluating reranking, we verified that the relevant document was present in the F0 Top-20 candidate pool.
- **Candidate-Pool Recall@20**: 1.000 (n=6). The relevant document was successfully preserved in the Top-20 pool for all positive cases, meaning reranking was mathematically possible.

## 6. Overall Metrics
| Metric | F0 (RRF) | F3 (MedCPT Cross-Encoder) | n |
| :--- | :--- | :--- | :--- |
| **Recall@5** | 0.667 | 1.000 | 6 |
| **MRR** | 0.667 | 0.867 | 6 |

## 7. Domain Metrics
| Domain Sub-Metric | F0 Recall@5 | F3 Recall@5 | n |
| :--- | :--- | :--- | :--- |
| **DDI Evidence** | 1.000 | 1.000 | 2 |
| **ADE Evidence** | 0.333 | 1.000 | 3 |
| **Medication Safety** | 1.000 | 1.000 | 1 |

*Finding: On the V2.1 ADE positive subset, F3 retrieved the labelled evidence cases within Top-5 more often than F0.*

## 8. Difficulty Metrics
| Query Difficulty | F0 Recall@5 | F3 Recall@5 | n |
| :--- | :--- | :--- | :--- |
| **PARAPHRASE** | 1.000 | 1.000 | 2 |
| **CYP_DDI** | 1.000 | 1.000 | 1 |
| **MECHANISM** | 0.000 | 1.000 | 1 |
| **SYNONYM** | 1.000 | 1.000 | 1 |
| **MULTI_ENTITY** | 0.000 | 1.000 | 1 |

## 9. DDI Analysis
F3 maintained 1.000 (n=2) DDI Evidence Recall, ensuring semantic relevance did not break existing exact interactions.

## 10. ADE Analysis
F3 improved ADE Evidence Recall from 0.333 (n=3) to 1.000 (n=3).

## 11. High-Risk Analysis
- **High-Risk (R3) Safety Cases**: F0=0.667, F3=1.000 (n=3)
*Finding: On the V2.1 high-risk subset, F3 retrieved all currently labelled positive cases within Top-5, compared with the F0 baseline.*

## 12. Entity Analysis
- **Top-1 Correct Entity Rate**: F0=0.667, F3=0.833 (n=6)
*Finding: Entity-level preservation was independently established and improved under F3.*

## 13. Authority Analysis
- **Relevant Authoritative Top-5 Rate**: F0=0.667, F3=1.000 (n=6)

## 14. Hard-Negative Analysis
- **Hard-Negative Rank (`e-12`, noise doc `42062777`)**: 
  - F0 Rank: 2
  - F3 Rank: 3
  - Relevant: False

## 15. Rank Recovery
- **Recovered by F3 (F0 > 5 AND F3 <= 5)**: 2 cases (`e-12`, `e-14`)

## 16. Rank Regression
- **Regression by F3 (F0 <= 5 AND F3 > 5)**: 0 cases

## 17. Latency
- **Total Latency**: ~1930 ms (CPU)

## 18. Statistical Analysis
Given n=6, statistical significance testing is severely underpowered. Paired significance will be tested on the V3 benchmark.

## 19. Metric Integrity Verification
All metrics above were strictly recomputed from case-level execution outputs and candidate metadata. Hard-coded assertions were completely eliminated. Provenance is documented in `phase2e_metric_provenance.md`.

## 20. Limitations
This remains a diagnostic benchmark. The perfect Recall@5 only confirms that the reranking mechanism works correctly on this subset. It is not final proof of general superiority.

## 21. Decision
**Decision: PRELIMINARY_SUPPORT**

MedCPT repaired the currently observed RRF ranking inversions on the V2.1 diagnostic subset.
We must now proceed to **V3 Confirmation**: running `F0 vs F3` on the stronger, large-scale V3 benchmark to mathematically validate this architecture before modifying the production `HybridRetrievalEngine`.