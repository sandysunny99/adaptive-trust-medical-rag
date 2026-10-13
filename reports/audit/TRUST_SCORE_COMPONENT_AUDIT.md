# Trust Score Component Audit

**Audit date:** 2026-10-13
**Code revision:** `298593f115bee9ff4c0c2f075077bbe5e5da897d` plus the current working-tree remediation
**Scope:** live application path and injected research orchestrator

## Formula and semantics

`AdaptiveTrustScorer` applies the frozen nine-factor weighted sum from
`config/trust.yaml`. Weights remain unchanged and sum to 1.0 for R0-R3.
Missing factors contribute zero to the numerator while the full denominator is
retained; the scorer records their names in `missing_factors`. Thresholds remain
R0=0.30, R1=0.45, R2=0.60, and R3=0.75.

| Factor | Source in current live path | Scale | Missing behavior | Gate/weight |
|---|---|---:|---|---|
| `source_authority` | `Candidate.source_authority`, populated from corpus metadata | 0..1 | scorer records missing only if absent | weighted and source floor |
| `query_relevance` | `Candidate.metadata["query_relevance"]` when supplied | 0..1 | no invented default; recorded missing | weighted |
| `evidence_quality` | `Candidate.metadata["evidence_quality"]` when supplied | 0..1 | no authority-score substitution; recorded missing | weighted |
| `freshness` | `Candidate.metadata["freshness_score"]` | 0..1 | recorded missing if absent | weighted |
| `consistency` | `1 - poisoning_score` | 0..1 | derived from candidate | weighted |
| `entity_match` | canonical medication names with word-boundary matching | 0..1 | zero when no canonical name matches | weighted |
| `population_match` | `Candidate.metadata["population_match"]` when supplied | 0..1 | recorded missing | weighted |
| `anti_poisoning` | `1 - poisoning_score`, after provenance/hash checks | 0..1 | derived from candidate | weighted |
| `anti_injection` | `1.0` only for text accepted by `PromptInjectionDetector` | 0..1 | blocked evidence is not eligible | weighted and hard security filter |

## Propagation

The live path is:

`retrieval_engine.retrieve` → provenance/hash and retrieved-text injection
checks → `TrustFactorScores` → `AdaptiveTrustScorer.score` →
minimum-trust aggregate over eligible evidence → SSE `trust` event and final
response.

The response now preserves `missing_factors`, `score_breakdown`, `weights`, and
`config_hash`. The aggregate score is the minimum score among scored candidates,
not the maximum single chunk score. Claim verification independently applies the
minimum trust of cited chunks.

The research orchestrator now consumes explicit metadata for relevance,
evidence quality, freshness, and population match instead of silently
substituting constants. Its existing eligibility gate remains separate from
the live application route.

## Authority and freshness

Authority is still source-specific through `source_authority` and the source
validation layer; it is not a universal freshness proxy. The current live
corpus provides authority and freshness metadata, but does not provide
`evidence_quality`, `query_relevance`, or `population_match` for every item.
Those factors therefore remain explicitly missing for such candidates. This is
honest engineering behavior, not experimental evidence that the factors are
measured.

## Regression evidence

- `tests/test_trust_scorer.py`: range validation, missing-factor semantics,
  formula, thresholds, and gate behavior.
- `tests/test_rag_orchestrator.py`: eligibility and end-to-end gate behavior.
- `tests/e2e/test_v6_c7_image_full_medical_rag.py`: live SSE trust metadata,
  missing-factor list, config hash, and score breakdown.
- Focused run after remediation: **61 passed, 182 warnings, exit code 0**.

## Remaining limitation

The live corpus needs an approved, traceable method for measuring
`query_relevance`, `evidence_quality`, and `population_match`. No constant
default has been introduced to make scores look complete. A scientific
evaluation must define and freeze those measurements before reporting trust
comparisons.
