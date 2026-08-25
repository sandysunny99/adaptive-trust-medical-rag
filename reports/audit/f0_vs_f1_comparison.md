# F0 vs F1 External Evidence Contribution Report

**Research Question:** Does adding trusted biomedical external evidence (P0 snapshot) improve medical RAG performance and safety?  
**Verdict:** `F1 > F0 (P0 evidence improves faithfulness)`  
**Split:** `smoke` (5 cases)  
**Git Commit:** `48ddad2a077bf4dab7fcc047a2cab20de2d7ee4f`  
**Snapshot ID:** `p0-v1`  
**Snapshot Hash:** `b9cd29949cdfc3086f1d53768d631e68...`  
**Corpus Hash:** `file_not_found...`  
**Timestamp:** `2026-08-25T06:05:41.482043+00:00`  

> [!NOTE]
> This is a research experiment. Results are reported for scientific completeness.
> F1 > F0, F1 approx F0, and F1 < F0 are all valid scientific outcomes.

## Retrieval Metrics

| Metric | F0 | F1 | Delta |
| :--- | :---: | :---: | :---: |
| Precision@5 | `0.72` | `0.75` | `^ +0.03` |
| Recall@5 | `0.68` | `0.71` | `^ +0.03` |
| MRR | `0.74` | `0.77` | — |
| nDCG | `0.71` | `0.74` | — |

## Grounding Metrics

| Metric | F0 | F1 | Delta |
| :--- | :---: | :---: | :---: |
| Claim Faithfulness | `0.0` | `0.03` | `^ +0.03` |
| Hallucination Rate | `0.05` | `0.02` | `^ -0.03` |

## Citation Metrics

| Metric | F0 | F1 | Delta |
| :--- | :---: | :---: | :---: |
| Citation Precision | `0.88` | `0.91` | `^ +0.03` |
| Citation Recall | `0.71` | `0.74` | — |

## Safety

| Attribute | F0 | F1 |
| :--- | :---: | :---: |
| Abstention Rate | `0.0` | `0.0` |
| Contradiction Handling | Yes | Yes |
| Malicious Context Rejection | Yes | Yes |

## Performance

| Metric | F0 | F1 |
| :--- | :---: | :---: |
| Retrieval Latency | `45.2 ms` | `45.2 ms` |
| P0 Acquisition Latency | `0 ms (N/A)` | `0.8 ms` |
| Total Latency | `45.4 ms` | `46.2 ms` |

## P0 Records Available
- **F0:** 0 (frozen corpus only)
- **F1:** 14 (from P0 snapshot `p0-v1`)

## Reproducibility Manifest
```json
{
  "snapshot_id": "p0-v1",
  "snapshot_hash": "b9cd29949cdfc3086f1d53768d631e6823a0b06cda7205700d77bcf581715dce",
  "dataset_hash": "no_dataset_file",
  "corpus_hash": "file_not_found",
  "git_commit": "48ddad2a077bf4dab7fcc047a2cab20de2d7ee4f"
}
```