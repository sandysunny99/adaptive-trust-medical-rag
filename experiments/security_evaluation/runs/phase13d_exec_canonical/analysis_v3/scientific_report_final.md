## A. Descriptive Results
Across the 20 authorization-eligible evaluation cases, observed UAR decreased from 20/20 (1.0000) in the baseline adapter to 10/20 (0.5000) in the hardened adapter.
Observed absolute UAR difference = 0.5000 (50.0 percentage points).
Observed relative UAR reduction = 50.0%.
ABR: Baseline 0/90 -> Hardened 11/90
ADR: Baseline 0/90 -> Hardened 11/90
FPR: Baseline 0/20 -> Hardened 0/20
PPR: Baseline 23/27 -> Hardened 23/27

## B. Paired Statistical Result
An exact two-sided McNemar test was applied to the paired authorization-eligible outcomes.
n01 = 0
n10 = 10
discordant pairs = 10
exact p-value = 0.001953
95% CI for the observed UAR difference using the protocol-approved method: [0.2252, 0.7748]

## C. Interpretation
The hardened adapter-level configuration exhibited fewer observed unauthorized-action successes than the baseline adapter across the evaluated authorization-eligible cases.

## D. Architectural Scope
This was an ADAPTER_LEVEL evaluation. The experiment directly exercised the implemented security-boundary components rather than a complete end-to-end generative RAG workflow.

## E. Limitations
* 110 structured cases
* 20 authorization-eligible cases for UAR
* adapter-level evaluation
* baseline security-boundary adapter
* no full end-to-end LLM RAG execution
* no real external evidence-service traversal
* single-turn case isolation
* structured/manual case taxonomy
* residual hardened UAR = 10/20