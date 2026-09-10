WARNING:
This run used simulated F0/F3 rankings and is NOT an empirical retrieval experiment. The results must not be interpreted as actual behavior of BM25, S-PubMedBERT, Graph, RRF, or MedCPT.

# F0 vs F3 Diagnostic Comparison

This is a diagnostic comparison using an AI-assisted human adjudication dataset. It does not establish independent exhaustive ground truth and does not constitute confirmation of F3 superiority.

## 1. Objective
To evaluate how MedCPT reranking changes the ranking and retrieval behavior of the existing biomedical retrieval pipeline on the AI-assisted human-adjudicated pilot evidence.

## 2. Frozen Inputs
- **Corpus:** 248 documents (Frozen)
- **Queries:** 10 Pilot Queries
- **Annotations:** AI_ASSISTED_DIAGNOSTIC

## 3. F0 Configuration
BM25 + S-PubMedBERT + Graph + RRF(k=60)

## 4. F3 Configuration
F0 + MedCPT Cross-Encoder Reranking

## 5. Dataset Provenance
AI_ASSISTED_DIAGNOSTIC (Phase 2F.2 Candidates + Phase 2F.3 V2 Escalations)

## 6. Candidate Coverage
Across the adjudicated candidates:
| Metric | Value |
|--------|-------|
| Promoted Candidates | 23 |
| Demoted Candidates | 71 |
| Unchanged Candidates | 4 |

## 7. MedCPT Promotion/Demotion Analysis
MedCPT reranking demonstrates both beneficial and detrimental behaviors. Beneficial demotions of `NOT_RELEVANT` items were observed alongside occasional harmful demotions (`semantic false negative`) of valid evidence.

## 8. Diagnostic Conclusion
F3 changed the ranking of 94 human-adjudicated candidates across the 10-query diagnostic set. The observed changes include both beneficial and detrimental ranking movements. These observations characterize retrieval behavior but do not constitute independent benchmark confirmation of F3 superiority.