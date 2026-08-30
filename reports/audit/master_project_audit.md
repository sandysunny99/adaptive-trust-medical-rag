# Master Project Audit Report

**Project:** Adaptive Trust-Aware Medical RAG: Mitigating Prompt Injection and Retrieval Hallucinations  
**Audit Date:** 2026-08-30  
**Git Commit at Audit:** `4a704f5`  

> **Audit Principle:** Documentation is not evidence. A passing test is not equivalent to research validation.

---

## Executive Summary

The project has built a **well-architected, well-tested research software platform**. The pipeline logic, security gates, trust scorer, hybrid retrieval, claim verifier, and evidence ingestion are all implemented in working Python code and covered by 645 passing unit tests.

**CRITICAL FINDING: The `LiveModelAdapter` does NOT call any external LLM provider.** It generates a deterministic template string locally (`f"Evidence-grounded response for query context: {prompt[:150]}..."`). All ablation variant runs (A-F), the 20-case smoke run (`live-smoke-v1`), and DM-mode F0/F1 are computational simulation — not live LLM evaluation.

This invalidates all faithfulness, hallucination rate, and claim verification results across every named experiment. The project is **engineering-complete but experimentally unverified** for academic publication.

---

## 1. Architecture (Verified Chain)

```
sanitize_query()             security/sanitizer.py          VERIFIED IMPLEMENTATION
DrugNormalizer.normalize()   normalization/drug_normalizer   VERIFIED IMPLEMENTATION (live RxNorm)
classify_query_risk()        trust_scoring/trust_scorer      VERIFIED IMPLEMENTATION
HybridRetrievalEngine        retrieval/hybrid_retrieval      VERIFIED IMPLEMENTATION
AdaptiveTrustScorer          trust_scoring/trust_scorer      VERIFIED IMPLEMENTATION
EvidenceEligibilityGate      orchestrator/rag_orchestrator   VERIFIED IMPLEMENTATION
LLMBackend (Protocol)        orchestrator/rag_orchestrator   VERIFIED (protocol only)
  LiveModelAdapter           evaluation/live_variants L149   SIMULATION - NOT a real LLM
  Real SDK (Gemini/OpenAI)   NOT IMPLEMENTED                 MISSING
AnswerSafetyGate             verification/claim_verifier     VERIFIED IMPLEMENTATION (rule-based)
```

---

## 2. Evidence Classification Table

| Result | Source | Execution | Evidence Level | Paper? |
|---|---|---|---|---|
| Canonical R1 trace | canonical_r1_trace_v2.json | Pipeline test | PARTIALLY VERIFIED | ⚠️ With caveats |
| 5-case live validation | five_case_validation.md | Mock pipeline | SIMULATION | NO |
| 20-case smoke run | live-smoke-v1/ (execution_type: simulation) | SIMULATION | SIMULATION | NO |
| P0 live API verification | p0-v1/manifest.json (SHA-256 hashed) | VERIFIED LIVE | VERIFIED LIVE EXECUTION | YES (connectivity only) |
| F0/F1-v1 | f0-f1-v1/ | Hard-coded p0_boost=0.03 | SIMULATION | NO |
| F0/F1-DM retrieval metrics | f0-f1-v2/summary.json | Real hybrid+trust | ENGINEERING EXPERIMENT | YES (retrieval only) |
| F0/F1-DM faithfulness/hallucination | f0-f1-v2/summary.json | Mock answer | SIMULATION | NO |
| Ablation A-F | Not yet run at scale | Mock | SIMULATION | NO |

---

## 3. LiveModelAdapter — Critical Finding

**File:** `src/adaptive_trust_medical_rag/evaluation/live_variants.py`  
**Line 149:**
```python
response_text = f"Evidence-grounded response for query context: {prompt[:150]}..."
```

No HTTP call. No API key. No real language model. The response is a deterministic string concatenation.

**Consequence:** All reported `faithfulness`, `hallucination_rate`, `citation_precision` values from the mock verifier operating on this template response are **not measures of LLM quality** — they reflect the lexical alignment of a 160-character template against evidence corpus text.

**`live-smoke-v1/summary.json` confirms:**
```json
"execution_type": "simulation",
"execution_backend": "mock",
"runtime_verified": false
```

---

## 4. Variant B/C Confound

Variants B (`_run_variant_b`) and C (`_run_variant_c`) both call:
```python
cands = self.retriever.retrieve(case.query, top_k=5)
```
on the same `HybridRetrievalEngine` with the same corpus. The logged metadata differs (`bm25_called: True/False`) but the underlying retrieval is identical. **B and C produce identical retrieval results in the current code.**

---

## 5. Trust Model — Accurate Characterization

**Type:** Risk-stratified fixed-weight linear scoring heuristic  
**Source:** `config/trust.yaml` (config-driven, not learned)  
**9 factors:** source_authority, query_relevance, evidence_quality, freshness, consistency, entity_match, population_match, anti_poisoning, anti_injection  
**Thresholds:** R0=0.30, R1=0.45, R2=0.60, R3=0.75 (specification-driven, not data-tuned)

**Note:** The word "adaptive" refers to risk-class-dependent weight vector selection, not to a learned/trained adaptive model. Documentation must use accurate terminology.

**Metadata bug:** Trust weight values logged in ablation variant E/F output (`authority: 0.35, entity: 0.30`) do NOT match trust.yaml R1 weights (authority: 0.20, entity: 0.10). This is a hardcoded reporting artifact.

---

## 6. Claim Verifier — Accurate Characterization

**Type:** Rule-based lexical overlap (NOT NLI, NOT LLM-based)  
- Claim extraction: sentence splitter + pharmacological regex  
- Alignment: token overlap ratio, threshold 0.70  
- Citation check: `[Source N]` regex pattern  
- Contradiction: absolute-language regex patterns  

**Limitation:** Lexical overlap misses semantic equivalence. A claim about "VKORC1 inhibition" will not align with evidence about "Vitamin K epoxide reductase inhibition" despite identical meaning. This inflates hallucination_rate in any experiment and must be documented as a limitation.

---

## 7. Retrieval Architecture — Accurate Characterization

| Component | Implementation | Production-grade? |
|---|---|---|
| BM25 | Pure-Python Okapi (k1=1.5, b=0.75) | ✅ Yes |
| Dense | Pure-Python cosine, 7-word vocab | ❌ No — toy embedder |
| Graph | Hardcoded adjacency list | ⚠️ Prototype |
| RRF | k=60 | ✅ Yes |
| pgvector | NOT connected | ❌ Missing |
| Neo4j | NOT connected | ❌ Missing |
| Corpus size | 4 (F0) / 18 (F1) documents | ❌ Too small |

**SimpleEmbeddingModel vocabulary:** `["metformin", "aspirin", "warfarin", "dosage", "mechanism", "renal", "indication"]` — 7 words. Results from "dense retrieval" are binary presence matches, not semantic similarity.

---

## 8. Security State

### Implemented:
- Prompt injection: 25 deterministic regex patterns ✅
- PHI detection: SSN, MRN, DOB, phone, NPI ✅
- SHA-256 content hashing at ingestion ✅
- Source authority tiering ✅
- Pre-generation eligibility gate ✅
- Post-generation answer safety gate (rule-based) ✅

### NOT Tested / NOT Implemented:
- Adversarial document injection in retrieval corpus: NO experiment
- Unicode/homoglyph injection: NOT implemented
- Delimiter attacks: NOT implemented
- Multi-turn injection: NOT implemented
- Attack success rate metric: NOT measured
- Malicious API response poisoning: NOT tested

---

## 9. Literature State

**Current `reports/research/literature_review_2026.md`:** 4 unnamed paraphrases, no authors, no DOIs, no venues, no years.  
**Classification:** UNVERIFIED / DOCUMENTATION ONLY  
**Required:** 15–20 real, fully cited papers from 2023–2026 (title, authors, venue, year, DOI, findings, limitations, research gap)

---

## 10. Dataset State

| Split | File | Size Estimate | Origin | PHI? |
|---|---|---|---|---|
| smoke | Generated by make_smoke_dataset() | 20 cases | Synthetic | No |
| dev | tests/dev_dataset_v1.jsonl | ~100 cases | Synthetic | No |
| val | tests/val_dataset_v1.jsonl | ~200 cases | Synthetic | No |
| test | Not frozen | — | Synthetic | No |

**Test set leakage:** NOT PROVABLE FROM CURRENT REPOSITORY — threshold values were specified before seeing test data (design doc), but this cannot be fully verified from history.

---

## 11. CI/CD State

**`ci.yml` runs automatically:** ruff, bandit, gitleaks, pytest, alembic chain check, hook tests ✅  
**Does NOT run:** live LLM experiments, P0 live API validation, research ablations  
**Artifact retention:** JUnit XML retained for 30 days ✅  
**Trivy supply chain scan:** `trivy.yml` separate workflow ✅

---

## 12. P0 API State

**Verified live** at commit `48ddad2` (2026-08-25):
- PubMed: 3 records, SHA-256 hashes recorded ✅
- Europe PMC: 3 records, SHA-256 hashes recorded ✅
- RxNorm: 4 drug lookups ✅
- openFDA: 4 label lookups ✅
- Total snapshot: 14 records, frozen at `experiments/evidence_snapshots/p0-v1/`
- Snapshot hash: `b9cd2994...` ✅

**Limitation:** Only 3 PubMed records and 3 Europe PMC records retrieved. Not a comprehensive pharmacological evidence set.

---

## 13. Forensic Verifier — Independence Confirmed

`evaluation/forensic_verifier.py` imports only stdlib (`hashlib`, `json`, `re`, `pathlib`). Does NOT import any production module. **Genuinely independent.** ✅

---

## 14. Statistical Methodology Issues

- Paired design for F0/F1-DM: ✅ Correct
- Wilcoxon signed-rank: ✅ Correctly called
- Cohen's dz: ✅ Correct
- Bootstrap 95% CI: ✅ 1000 iterations
- **Missing:** Multiple testing correction for 7 simultaneous metrics
- **Missing:** Pre-registered primary outcome metric
- **Invalid:** Faithfulness/hallucination statistics computed from mock generation — must be removed from all tables

---

## 15. Publication Readiness

**Status: NOT READY**

| Requirement | Status |
|---|---|
| Real LLM integration | ❌ Missing |
| Meaningful evidence corpus | ❌ 4-18 documents (insufficient) |
| Valid faithfulness results | ❌ All from mock |
| Valid ablation A-F | ❌ All from mock + confound |
| Verified literature review | ❌ 0 verifiable citations |
| Frozen test set | ❌ Not yet defined |
| Final test run | ❌ Not yet executed |
| Multiple testing correction | ❌ Missing |
| Real semantic embeddings | ❌ Toy 7-word vocabulary |
| Adversarial security evaluation | ❌ Not run |

**What IS ready:**
- Complete pipeline architecture ✅
- Security controls (rule-based) ✅
- 645 unit tests ✅
- P0 live API connectivity ✅
- F0/F1 retrieval engineering result ✅
- Forensic auditor infrastructure ✅
- Reproducible snapshot replay ✅

---

## 16. Priority Backlog

### P0 — Blocks research validity
1. Implement `RealLLMAdapter` with actual Gemini/OpenAI API call
2. Fix Variant B/C confound (separate retriever configurations)
3. Expand evidence corpus to 100+ pharmacological chunks
4. Replace `SimpleEmbeddingModel` with sentence-transformers
5. Rebuild literature review with 15-20 real verifiable papers

### P1 — Before publication
6. Re-run full A-F ablation with real LLM on dev split (100 cases)
7. Re-run F0/F1 with real LLM (F0/F1-LIVE)
8. Apply multiple testing correction; pre-register primary metric
9. Run adversarial security evaluation with poisoned documents
10. Freeze 500+ case test set; run once for final results

### P2 — Enhancement / Future work
11. Frontend UI for demonstration
12. SLM security variant G (if research question justified)
13. ClinicalTrials.gov integration
14. pgvector / Neo4j live integration

---

## 17. Final Answer: Minimum Remaining Work

> **What is the minimum remaining work to turn this repository into a defensible academic research project and demonstrable Medical RAG application?**

**Engineering (3-5 weeks):**
1. Real LLM adapter (1 week)
2. Evidence corpus expansion via P0 API bulk fetch (1 week)
3. Real semantic embedder integration (3 days)
4. Fix B/C confound (2 days)
5. Literature review rebuild (1 week, parallel)

**Experimental (2-3 weeks after engineering):**
6. Run real A-F ablation on dev split (1 week runtime + analysis)
7. Run real F0/F1-LIVE (2-3 days)
8. Adversarial security evaluation (1 week)

**Publication (2-3 weeks after experiments):**
9. Statistical analysis with corrections
10. Paper writing using only verified results
11. Final test set evaluation (once only)

**Total estimated remaining effort: 6-10 weeks of focused work.**
