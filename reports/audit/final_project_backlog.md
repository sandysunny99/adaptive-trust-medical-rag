# Final Project Backlog

**Date:** 2026-08-30  
**Based on:** master_project_audit.md (commit 4a704f5)

| Priority | Task | Type | Reason | Dependency | Risk | Must Finish Before |
|---|---|---|---|---|---|---|
| P0 | Implement RealLLMAdapter (Gemini/OpenAI SDK) | Engineering | LiveModelAdapter is a stub; all LLM quality metrics are invalid | None | HIGH - API costs, error handling | Any LLM quality experiment |
| P0 | Fix Variant B/C confound (separate retriever configs) | Engineering | B and C call identical retriever; experimental variable is metadata flag only | None | MEDIUM | Any ablation run |
| P0 | Replace SimpleEmbeddingModel with sentence-transformers | Engineering | 7-word vocabulary is not semantic similarity; dense retrieval results are not meaningful | None | MEDIUM | Dense retrieval experiments |
| P0 | Expand evidence corpus to 100+ chunks | Data | 4-18 documents insufficient for retrieval evaluation | P0 APIs verified | HIGH - data quality | Any retrieval experiment |
| P0 | Rebuild literature review with 15-20 real verifiable papers | Research | Current review has 0 verifiable citations; unacceptable for paper | None | MEDIUM | Paper writing |
| P1 | Run real A-F ablation on dev split (100 cases) with real LLM | Experiment | All current ablation results invalid | RealLLMAdapter, corpus expansion, B/C fix | HIGH | Final paper results |
| P1 | Re-run F0/F1 with real LLM (F0/F1-LIVE) | Experiment | DM-mode faithfulness/hallucination results are simulation | RealLLMAdapter | HIGH | Paper Section 5 |
| P1 | Apply multiple testing correction (Bonferroni/BH) | Statistics | 7 metrics tested without correction; inflated false-discovery risk | Valid experiment results | LOW | Paper statistics section |
| P1 | Pre-register primary outcome metric | Research | No primary metric defined; all 7 reported equally | None | LOW | Final experiment |
| P1 | Run adversarial security evaluation (poisoned corpus) | Experiment | Attack success rate / malicious context influence rate not measured | Corpus expansion | HIGH | Security section |
| P1 | Fix trust metadata mismatch in ablation logs | Engineering | Logged weights (0.35/0.30) don't match trust.yaml (0.20/0.10) | None | LOW | Final ablation run |
| P1 | Define and freeze 500+ case test set | Data | Test set does not exist; cannot run final evaluation | Corpus expansion | HIGH | Final test run |
| P1 | Run final test evaluation exactly once | Experiment | Results must be traced to single frozen run | Frozen test set | HIGH | Paper |
| P2 | Frontend web UI (query + evidence + trust + citations display) | Engineering | Useful for demonstration; not required for paper | Full pipeline working | LOW | Demo / defense |
| P2 | SLM security variant G | Research | Only if G creates a meaningful research question beyond F | F complete | MEDIUM | If G is in scope |
| P2 | ClinicalTrials.gov API integration | Engineering | Assess unique evidence contribution vs P0 providers | P0 stable | LOW | Future work |
| P2 | pgvector live integration | Engineering | Currently pure-Python in-memory; not required for publication | None | LOW | Production deployment |
| P2 | Neo4j live graph | Engineering | Hardcoded adjacency is functional prototype; not required for paper | None | LOW | Future work |

## What NOT to Build Now

| Item | Reason |
|---|---|
| SLM (Variant G) | F is not yet validated; adding G is premature research overhead |
| ClinicalTrials.gov, Crossref, Semantic Scholar, OpenAlex | P0 providers not fully exploited yet; deferred until P0 proves insufficient |
| Extended graph knowledge base | Hardcoded edges are acceptable for current scope |
| Frontend React/Vue application | Paper, not product, is the immediate deliverable |
| Additional ablation variants beyond A-F | A-F covers all research hypotheses; adding variants increases experiment complexity without proportional insight |
| Raw LLM output caching | Premature optimization; implement after real adapter works |
