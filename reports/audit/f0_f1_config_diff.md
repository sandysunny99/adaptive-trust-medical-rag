# F0 / F1 Experimental Configuration Diff & Control Verification

| Configuration Element | F0 Setting | F1 Setting | Status |
| :--- | :--- | :--- | :---: |
| **Dataset & Cases** | 20 paired cases | 20 paired cases | IDENTICAL |
| **Pipeline Mode** | DETERMINISTIC_MOCK | DETERMINISTIC_MOCK | IDENTICAL |
| **Retrieval Architecture** | BM25 + Dense + RRF | BM25 + Dense + RRF | IDENTICAL |
| **Trust Scorer Weights** | Authority 0.35, Freshness 0.20, Entity 0.30, Rep 0.15 | Authority 0.35, Freshness 0.20, Entity 0.30, Rep 0.15 | IDENTICAL |
| **Risk Thresholds** | R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75 | R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75 | IDENTICAL |
| **Evidence Eligibility Gate** | Active (Pre-Generation) | Active (Pre-Generation) | IDENTICAL |
| **Answer Safety Gate** | Active (Post-Generation) | Active (Post-Generation) | IDENTICAL |
| **Evidence Backend** | `BASE_CORPUS` (4 docs) | `BASE_CORPUS_PLUS_P0` (4 base + 14 P0 docs) | **CONTROLLED EXPERIMENTAL VARIABLE** |

**Verdict:** `CONTROLLED EXPERIMENT — SINGLE INDEPENDENT VARIABLE VERIFIED`