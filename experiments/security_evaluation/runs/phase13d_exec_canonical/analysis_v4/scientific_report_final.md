# Phase 13D Scientific Results

## 1. Experimental Scope
This was an ADAPTER_LEVEL evaluation. The experiment directly exercised the implemented security-boundary components rather than a complete end-to-end generative RAG workflow.
The baseline is a security-boundary adapter.
The HARDENED condition evaluates component invocation across 110 structured cases, including 20 authorization-eligible cases.

## 2. Descriptive Results
Across the 20 authorization-eligible evaluation cases, observed UAR decreased from 20/20 (1.0000) in the baseline adapter to 10/20 (0.5000) in the hardened adapter.
Observed absolute UAR difference = 0.5000 (50.0 percentage points).
Observed relative UAR reduction = 50.0%.
* ABR: Baseline 0/90 -> Hardened 11/90
* ADR: Baseline 0/90 -> Hardened 11/90
* FPR: Baseline 0/20 -> Hardened 0/20
* PPR: Baseline 23/27 -> Hardened 23/27

## 3. Paired Statistical Result
An exact two-sided McNemar test was applied to the paired authorization-eligible outcomes.
* n01 = 0
* n10 = 10
* discordant pairs = 10
* exact p-value = 0.001953
* 95% Wald CI for paired difference (with continuity correction): [0.2252, 0.7748]

## 4. Attack-Family Results
| Family | N | Base Det | Hard Det | Base Blk | Hard Blk | Base FP | Hard FP |
|---|---|---|---|---|---|---|---|
| PROMPT_INJECTION | 35 | 0 | 0 | 0 | 0 | 0 | 0 |
| RETRIEVAL_POISONING | 25 | 0 | 1 | 0 | 1 | 0 | 0 |
| BOUNDARY_VIOLATION | 20 | 0 | 10 | 0 | 10 | 0 | 0 |
| PROVENANCE_ATTACK | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| BENIGN_CONTROL | 20 | 0 | 0 | 0 | 0 | 0 | 0 |

## 5. Hardened Failure Analysis
10 residual UAR failures: Group 1 (10 successes), Group 2 (10 residual failures where BASELINE and HARDENED both allowed unauthorized actions).

## 6. Interpretation
The hardened adapter-level configuration exhibited fewer observed unauthorized-action successes than the baseline adapter across the evaluated authorization-eligible cases.
This evidence is within the defined evaluation scope and does not prove real-world security effectiveness.

## 7. Limitations
* adapter-level architecture
* 110 structured cases
* 20 UAR-eligible cases
* synthetic/manual taxonomy
* no end-to-end LLM inference
* no external evidence-service traversal
* single-turn evaluation
* baseline abstraction
* residual hardened UAR 10/20