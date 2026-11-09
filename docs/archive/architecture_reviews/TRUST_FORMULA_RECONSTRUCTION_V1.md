# TRUST FORMULA RECONSTRUCTION

**Date:** 2026-10-03  

**Formula:** `Trust = Sum(Weight_i * Factor_i)`

## Reconstruction (Tier R3 Example)

| Factor | Weight | Runtime Value | Missing? | Contribution to Score |
|---|---|---|---|---|
| `authority` | 0.30 | Measured | No | `0.30 * value` |
| `query_relevance` | 0.10 | 0.0 | **YES** | `0.00` |
| `evidence_quality` | 0.25 | 0.0 | **YES** | `0.00` |
| `freshness` | 0.10 | Measured | No | `0.10 * value` |
| `consistency` | 0.10 | Measured | No | `0.10 * value` |
| `entity_match` | 0.10 | Measured | No | `0.10 * value` |
| `population_match` | 0.03 | 1.0 | No (Default) | `0.03` |
| `anti_poisoning` | 0.01 | Measured | No | `0.01 * value` |
| `anti_injection` | 0.01 | 1.0 | No (Constant) | `0.01` |

## Arithmetic Aggregates

- **Sum of configured weights:** `1.0`
- **Sum of missing contributions:** `0.10 + 0.25 = 0.35`
- **Max possible populated contribution:** `1.0 - 0.35 = 0.65`
- **Threshold for R3:** `0.75`
- **Reachability:** **IMPASSABLE**

*(Note: In R0, missing weights total 0.30, giving a max score of 0.70. For R1 and R2, missing weights total 0.35, giving a max score of 0.65.)*
