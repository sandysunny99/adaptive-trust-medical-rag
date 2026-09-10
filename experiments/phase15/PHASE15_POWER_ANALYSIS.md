# Phase 15 Power Analysis

## 1. Objective

Determine the minimum required sample size for Phase 15 to detect a statistically significant improvement in Security Failure Rate (SFR) between the Baseline and Hardened configurations, avoiding arbitrary numbers.

## 2. Assumptions for Planning

Based on architectural scope and previous adapter-level behaviors, we estimate:
- **Baseline SFR:** 40% (high susceptibility to prompt injection, poisoning, and hallucinated claims without active gates).
- **Hardened SFR:** 10% (accounting for residual unknown attack vectors or complex medical hallucinations that evade Gate 2).
- **Expected Absolute Reduction ($\Delta$):** 30 percentage points.
- **Proportion of Discordant Pairs:** Assuming the mechanisms successfully catch failures the baseline misses, we expect approximately 35% of the total cases to be discordant (i.e., Baseline=Fail, Hardened=Safe).
- **Alpha ($\alpha$):** 0.05 (two-tailed).
- **Target Power ($1 - \beta$):** 0.80 (80%).

## 3. Sample Size Calculation

Using McNemar's exact test power calculations for paired proportions:
To achieve 80% power at $\alpha=0.05$ detecting a difference between 40% and 10% failure rates, requiring a minimum number of discordant pairs $n_d$:
- Required discordant pairs $\approx$ 18.
- Given an expected 35% discordance rate in the sampled dataset, total $N \approx 18 / 0.35 \approx 51$ cases minimum.

However, to ensure robust evaluation across all 6 attack/scenario families (Injection, Poisoning, Boundary, Unsupported, Contradiction, Benign) and maintain tight confidence intervals:
**Recommended Total N:** 200 cases.
(approx. 30-35 cases per family).

## 4. Sensitivity Scenario

If the Hardened system performs less optimally (e.g., reduces SFR from 40% to only 25%), $\Delta = 15\%$.
To detect a 15% difference with 80% power assuming 25% discordance, $N \approx 140$.
The target of **200 cases** safely powers the experiment even if the effect size is lower than expected.
