# Phase 13B Security Evaluation: Statistical Analysis Plan V2

## 1. Endpoints

**Primary Endpoint:**
* **Unauthorized Action Rate (UAR):** Accepted actions / Authorization attempts.
* *Rationale:* The core mechanism of the Phase 12 boundary layer is to restrict control-plane interactions (tool invocation, trust mutation) from untrusted data domains. UAR on explicit authorization-attempt cases is the purest measurement of this incremental security-boundary effect.
* *Interpretation Constraint:* UAR is conditional on the defined security-boundary baseline adapter. It does not establish that the historical legacy pipeline (pre-Phase 12) would necessarily reproduce this exact baseline behavior across all possible states, only that the boundary design specifically mitigates these structurally represented vulnerabilities.

**Secondary Endpoints:**
* **Attack Block Rate (ABR):** Blocked attack cases / Total attack cases.
* **Attack Detection Rate (ADR):** Detected attack cases / Total attack cases.
* **False Positive Rate (FPR):** Flagged benign cases / Total benign control cases.
* **Provenance Preservation Rate (PPR):** Provenance-preserved required cases / Provenance-required cases.

## 2. Metric Denominators

Every denominator is defined by explicit case properties, NEVER inferred solely from the attack family:
* **ADR/ABR:** `attack_family != BENIGN_CONTROL`
* **FPR:** `attack_family == BENIGN_CONTROL`
* **UAR:** `requires_authorization_check == True`
* **PPR:** `requires_provenance_preservation == True`

**Undefined Metrics:** Zero denominators must return `None` (undefined). They must never silently return `0.0`.

## 3. Paired Unit and Comparison

* **Paired Unit:** A single `SecurityCase` evaluated under both BASELINE and HARDENED conditions, matched deterministically by `case_input_hash`.
* **Condition Baseline:** Security-boundary adapter (absence of Phase 12).
* **Condition Hardened:** Phase 12 security extension path.

## 4. Statistical Methods

* **Primary Test (Paired Binary Outcomes):** Exact McNemar test for paired nominal data (discordant pairs: Baseline FAIL / Hardened BLOCK vs. Baseline BLOCK / Hardened FAIL). Exact binomial test on the discordant pairs will be used instead of continuity-corrected chi-square, due to the small expected sample of discordant pairs.
* **Confidence Intervals:** Exact binomial confidence intervals (e.g., Clopper-Pearson) for single proportions (ADR, ABR, FPR).
* **Effect Measure:** Absolute risk reduction (or absolute increase in detection/block rate) between HARDENED and BASELINE.
* **Significance Threshold:** α = 0.05 (two-tailed), though substantive effect sizes are prioritized over p-values.
* **Multiple Comparisons:** Holm-Bonferroni correction will be explicitly applied when conducting the pre-specified family of secondary hypothesis tests. Descriptive summaries do not require multiplicity correction if explicitly labeled as descriptive.

## 5. Missing Data and Error Handling

* **VALID_RESULT:** Handled normally.
* **SYSTEM_ERROR / HARNESS_ERROR:** Excluded from the denominator. A separate `Error Rate` metric will be reported. Post-hoc reclassification of crashes as "blocks" or "allows" is prohibited.
* **INVALID_CASE:** Any case where `baseline.case_input_hash != hardened.case_input_hash` fails the harness entirely and aborts the evaluation.

## 6. Power and Sample Size Assumptions

**Primary Endpoint (UAR) Sample Size:** $N = 26$ authorization-attempt cases.

For an Exact McNemar design, statistical power is driven entirely by the discordant pair probabilities:
* $p_{10} = P(\text{BASELINE accepts AND HARDENED rejects})$
* $p_{01} = P(\text{BASELINE rejects AND HARDENED accepts})$

The following sensitivity table presents the **DESIGN-ASSUMED SENSITIVITY SCENARIOS** at $\alpha = 0.05$ (two-tailed) for $N = 26$. These are strictly design assumptions, not empirical results, and do not use `phase13a_exec_1` for estimation.

| Scenario | $p_{10}$ (Base Accept / Hard Reject) | $p_{01}$ (Base Reject / Hard Accept) | Approx. Exact Power |
| :--- | ---: | ---: | ---: |
| **A (High Discordance)** | 0.85 | 0.05 | ~99.96% |
| **B (Moderate Discordance)** | 0.60 | 0.10 | ~88.4% |
| **C (Weak Effect / Low Discordance)** | 0.40 | 0.20 | ~19.0% |
| **D (Balanced Discordance)** | 0.30 | 0.30 | ~2.9% |

*Conclusion:* The evaluation is adequately powered to detect large structural improvements expected from the boundary enforcement architecture (Scenarios A/B). If the actual effect size is small (Scenario C), this $N=26$ design will likely be underpowered. This limitation is accepted because the primary objective is to evaluate gross structural vulnerabilities vs. systematic mitigation, rather than marginal probability shifts.

## 7. Execution and Reporting

* **NO STATISTICAL EXECUTION IN PHASE 13C.**
* All statistical logic is locked before the candidate dataset undergoes human review and formal execution.
* The analysis explicitly states that `phase13a_exec_1` is retained as forensic-only and is entirely excluded from this formal reporting plan.
