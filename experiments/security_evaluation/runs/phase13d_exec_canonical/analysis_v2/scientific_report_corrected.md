# Scientific Report (Corrected)
## A. DESCRIPTIVE RESULTS
* UAR 1.0 -> 0.5 (absolute reduction = 0.5, relative reduction = 50%)
* ABR 0 -> 11/90
* ADR 0 -> 11/90
* FPR 0/20 -> 0/20
* PPR 23/27 -> 23/27

## B. STATISTICAL RESULTS
* Exact McNemar test (n01=0, n10=10) yielded p-value = 0.001953.
* Corrected 95% CI for paired difference: [0.2252, 0.7748].

## C. INTERPRETATION
The hardened adapter-level configuration exhibited fewer unauthorized-action successes than the baseline adapter on the evaluated authorization-eligible cases.

## D. LIMITATIONS
* 110 structured cases (20 authorization-eligible cases for UAR).
* Adapter-level rather than end-to-end evaluation.
* Baseline is a logical/security-boundary adapter, not a real insecure production system.
* No real LLM inference or external evidence-service traversal.
* Residual HARDENED UAR = 10/20 (50%).