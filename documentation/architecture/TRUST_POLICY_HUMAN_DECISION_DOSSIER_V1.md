# TRUST MISSING-VALUE POLICY: HUMAN DECISION DOSSIER

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  

## The Decision

The variables `query_relevance` and `evidence_quality` default to `0.0` and are unpopulated in the current architecture. This dossier provides the scientific and mathematical impact of the three possible research policies.

---

## A. What happens technically?

- **Option A (Imputation):** Requires injecting retrieval metrics (e.g., RRF scores) into the `Candidate` object and writing mapping logic in `rag_orchestrator.py` to extract and normalize those values into the `[0,1]` range for the trust formula.
- **Option B (Renormalization):** Requires mathematically altering `trust.yaml` to remove the two fields and proportionally increase the remaining 7 weights to sum to 1.0.
- **Option C (Keep 0.0):** Requires no code changes.

## B. What happens mathematically?

| Tier | Configured Weight Sum | Missing Weight | Max Score (Opt C) | Reachable? (Opt C) |
|---|---|---|---|---|
| **R0** | 1.00 | 0.30 | 0.70 | YES (Threshold 0.30) |
| **R1** | 1.00 | 0.35 | 0.65 | YES (Threshold 0.45) |
| **R2** | 1.00 | 0.35 | 0.65 | YES (Threshold 0.60) |
| **R3** | 1.00 | 0.35 | 0.65 | **NO** (Threshold 0.75) |

*Mathematical Proof:* In Risk Tier R3, weights are: authority(0.30), query_rel(0.10), ev_qual(0.25), freshness(0.10), consist(0.10), ent_match(0.10), pop_match(0.03), anti_poison(0.01), anti_inject(0.01). If query_rel (0.10) and ev_qual (0.25) are exactly 0.0, the sum of all remaining maximums is 0.65. The R3 gate requires 0.75.

## C. What happens experimentally?

- **Option A:** R3 becomes passable. However, because different retrieval engines (BM25 vs Vector vs Cognee) have vastly different score distributions, trust eligibility becomes tightly coupled to the specific retrieval engine being tested.
- **Option B:** R3 becomes passable. The penalty is removed universally.
- **Option C:** High-risk (R3) queries will consistently trigger controlled abstention due to insufficient measured trust.

## D. What happens to historical reproducibility?

- **Option A & B:** Absolute trust scores will diverge from the frozen Gate 5 baseline.
- **Option C:** Perfectly preserves Gate 5 reproducibility.

## E. What happens to Baseline vs Cognee comparability?

- **Option A:** **CRITICAL RISK.** Deriving trust from a retrieval score creates circularity. If Cognee produces inherently different similarity distributions than BM25, the Trust Layer will gate candidates differently based solely on the engine, contaminating the independent measurement of hallucination reduction.
- **Option B & C:** Preserves independent comparability. Trust is evaluated completely orthogonal to the retrieval engine's ranking confidence.

## F. What happens to trust-model interpretation?

- **Option A:** Redefines "Trust" to include "Retrieval Confidence".
- **Option B:** Redefines the architecture from a 9-factor holistic model to a 7-factor reduced model.
- **Option C:** Maintains the 9-factor model but asserts that the system's inability to measure specific factors correctly penalizes the overall trust confidence (Fail-Closed).

## G. What changes in the thesis methodology?

- **Option A:** Requires formally documenting that Trust is now partially retrieval-dependent.
- **Option B:** Requires amending the core architecture document to reflect 7 factors.
- **Option C:** Requires documenting that the measurement deficiency restricts the operational envelope (R3 impassable).

## H. What artifacts must change?

- **Option A:** `rag_orchestrator.py`, Architecture Doc, Protocol.
- **Option B:** `trust.yaml`, Architecture Doc, Protocol.
- **Option C:** Architecture Doc (Limitations section).

## I. What experiments must be rerun?

- **Option A & B:** Gate 5 baseline must be rerun to establish a valid comparison baseline for the Cognee benchmark.
- **Option C:** None.

## J. What assumptions would need to be documented?

- **Option A:** Assumes normalized retrieval scores across vastly different mathematical vector spaces are fairly comparable. Assumes no formal evidence quality metadata exists.
- **Option B:** Assumes the 7 remaining factors are sufficient to gate medical evidence safely.
- **Option C:** Assumes that missing a measurement should strictly penalize trust (Safety-first).

---

## Decision Matrix

| Decision Criterion | Option A | Option B | Option C |
|--------------------|----------|----------|----------|
| Historical reproducibility | Broken | Broken | Maintained |
| Scientific interpretability | Compromised by circularity | High (7-factor) | High (Fail-closed) |
| Trust-model fidelity | Altered | Altered | Maintained |
| Threshold validity | Restored | Restored | Degraded (R3 locked) |
| Risk-tier reachability | All reachable | All reachable | R0-R2 reachable |
| Retrieval independence | Lost | Maintained | Maintained |
| Cognee comparability | Contaminated | Clean | Clean |
| Implementation complexity| High | Low | None |
| Need to rerun prior exp. | Yes | Yes | No |
| Risk of introducing bias | High (Retrieval bias) | Low | Low (Conservative bias)|
