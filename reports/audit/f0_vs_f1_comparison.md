# F0 vs F1 Empirical Evidence Contribution Report (v2)

**Experiment:** `f0-f1-v2`  
**Pipeline Mode:** `DETERMINISTIC-MOCK`  
**Git Commit:** `97d070cbc9e4b06ed6e1d32a9c2d706109b2a48f`  
**Evaluated Cases:** `20` paired cases  

> [!IMPORTANT]
> This experiment evaluates the retrieval and evidence contribution difference under deterministic mock execution.
> It does NOT make claims regarding live LLM answer generation quality.

## Empirical Metric Comparison

| Metric | F0 (Base Corpus) | F1 (Base + P0 Snapshot) | Delta | Wilcoxon p | Cohen's dz | 95% Bootstrap CI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Precision@5 | `0.2400` | `0.6100` | `+0.3700` | `0.0003` | `1.3338` | `[0.2600, 0.5000]` |
| Recall@5 | `0.8250` | `0.9000` | `+0.0750` | `0.2871` | `0.4094` | `[0.0000, 0.1500]` |
| Claim Faithfulness | `0.3917` | `0.3543` | `-0.0373` | `0.1416` | `-0.4344` | `[-0.0727, -0.0001]` |
| Hallucination Rate | `0.6083` | `0.6457` | `+0.0373` | `0.1416` | `0.4344` | `[0.0001, 0.0727]` |
| Citation Precision | `0.5125` | `0.7050` | `+0.1925` | `0.0062` | `0.7577` | `[0.0892, 0.3017]` |
| Citation Recall | `0.8750` | `0.9500` | `+0.0750` | `0.2871` | `0.4094` | `[0.0000, 0.1500]` |
| Total Latency (ms) | `0.37` | `1.30` | `+0.93` | — | — | — |

## P0 Snapshot Utilization in F1

- **P0 Chunks Retrieved per Case (Mean):** `2.90`
- **P0 Chunks Eligible/Accepted (Mean):** `2.90`