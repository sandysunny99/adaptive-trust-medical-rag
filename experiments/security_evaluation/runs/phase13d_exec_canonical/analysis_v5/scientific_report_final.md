# Phase 13D Final Scientific Results

## 1. Experimental Scope
This was an adapter-level evaluation across 110 structured cases, including 20 authorization-eligible cases. The baseline was a security-boundary adapter, while the hardened condition evaluated direct component invocation. This was not an end-to-end generative RAG evaluation.

## 2. Primary Result
Across the 20 authorization-eligible evaluation cases, observed UAR decreased from 20/20 (1.0000) in the baseline adapter to 10/20 (0.5000) in the hardened adapter.
Observed absolute difference in UAR = 0.5000 (50.0 percentage points).
Observed relative reduction in UAR = 50.0%.

## 3. Paired Statistical Analysis
* McNemar table: n00=0, n01=0, n10=10, n11=10
* discordant pairs: 10
* exact p-value: 0.001953
* CI method: Wald interval for paired difference with continuity correction (analyst-selected supplementary CI method)
* CI parameter: difference in observed proportions
* Protocol CI status: The protocol explicitly requires reporting confidence intervals but DOES NOT specify the exact estimator or parameter approach. Thus, CI protocol alignment is PARTIAL.

## 4. Secondary Metrics
* ABR: Baseline 0/90 -> Hardened 11/90
* ADR: Baseline 0/90 -> Hardened 11/90
* FPR: Baseline 0/20 -> Hardened 0/20
* PPR: Baseline 23/27 -> Hardened 23/27

## 5. Attack-Family Results
| Family | N | Base Det | Hard Det | Base Blk | Hard Blk | Base FP | Hard FP |
|---|---|---|---|---|---|---|---|
| PROMPT_INJECTION | 35 | 0 | 0 | 0 | 0 | 0 | 0 |
| RETRIEVAL_POISONING | 25 | 0 | 1 | 0 | 1 | 0 | 0 |
| BOUNDARY_VIOLATION | 20 | 0 | 10 | 0 | 10 | 0 | 0 |
| PROVENANCE_ATTACK | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| BENIGN_CONTROL | 20 | 0 | 0 | 0 | 0 | 0 | 0 |

## 6. UAR Improvement Analysis
There were 10 cases where the hardened condition improved upon the baseline by blocking an unauthorized action. These cases successfully demonstrated component invocation outcomes under the adapter boundary.

## 7. Residual Failure Analysis
There were 10 cases where hardening still allowed unauthorized action, leaving a residual UAR of 10/20. These represent evaluation scenarios where the boundary either did not block the request or the adapter permitted the flow.

## 8. Interpretation
The hardened adapter-level configuration exhibited fewer observed unauthorized-action successes than the baseline adapter across the evaluated authorization-eligible cases. This result is limited to the defined adapter-level evaluation and does not establish end-to-end real-world security effectiveness.

## 9. Thesis Claim Audit
| Claim | Evidence | Strength | Allowed Wording | Disallowed Wording |
|-------|----------|----------|-----------------|--------------------|
| Adapter-Level UAR Reduction | UAR 20/20 vs 10/20 (p=0.001953) | Strong (within evaluation context) | 'The Phase 13D adapter-level paired evaluation observed a reduction in unauthorized-action success rate from 100% (20/20) under the baseline adapter to 50% (10/20) under the hardened condition...' | 'The RAG reduced attacks by 50%' |
| End-to-End System Security | None | None | N/A | 'The system is 50% more secure', 'Real-world security improved by 50%', 'End-to-end effectiveness was validated' |
| Component Invocation | attack_family routing inside adapter | Partial (indirectly inferred) | 'The boundary violations were routed to the AuthorizationBoundary component...' | 'Component execution traces definitively prove the AuthorizationBoundary alone blocked the attacks.' |

## 10. Limitations
* 110 structured cases
* 20 UAR-eligible cases
* adapter-level execution
* baseline abstraction
* no end-to-end LLM/RAG execution
* no external evidence-service traversal
* single-turn isolation
* structured/manual taxonomy
* residual hardened UAR = 10/20
* finite case-set scope
* Component traceability is indirectly inferred from attack-family routing.
* The confidence interval is an analyst-selected supplementary method (Wald continuity-corrected), as the protocol does not lock an exact mathematical estimator.