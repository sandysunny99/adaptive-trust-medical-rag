# GATE 5 RERUN SCOPE ANALYSIS

**Date:** 2026-10-03  

## 1. What triggers a rerun?
Any mathematical change to the `AdaptiveTrustScorer` (imputation, renormalization, or new continuous signals) invalidates all previously recorded trust scores in Gate 5.

## 2. What exactly must be rerun?
If a rerun is triggered, it is **not** just a single unit test. The scope encompasses:
- The entire **92-run Gate 5 Offline Baseline Benchmark**.
- This includes every experimental permutation of queries against the `FROZEN_CORPUS_2.0.0` using BM25, S-PubMedBERT, and RRF (k=60).
- All trust scores, eligibility decisions, and abstention logs must be regenerated and re-verified.

## 3. Why? (Baseline vs Cognee Comparability)
The entire purpose of the RAG benchmark is to compare the Baseline retrieval performance against Cognee. If the Cognee runs use a different Trust Formula (e.g., a 7-factor renormalized model) than the recorded Gate 5 Baseline runs (which used the 9-factor missing=0.0 model), the comparison is scientifically invalid.

## 4. Conclusion
If the researcher selects **Trust Option A or B**, or **Anti-Injection Option B or C**, the project roadmap must insert a massive baseline re-execution step before proceeding to Gate C.
