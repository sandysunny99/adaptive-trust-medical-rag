# F0/F1 Research Integrity & Empirical Evidence Report

## 1. Experiment Classification
**Classification:** `PRELIMINARY EMPIRICAL RESULT — DETERMINISTIC MOCK`  
**Experiment ID:** `f0-f1-v2`  
**Timestamp:** `2026-08-25T06:40:11.907113+00:00`  

## 2. Experimental Rigor & Controls
- **Paired Case Execution:** Every evaluation case was independently executed through both F0 and F1.
- **Zero Hard-Coded Metrics:** All aggregate numbers and paired differences are derived from `case_results.jsonl`.
- **P0 Evidence Grounding:** F1 uniquely accesses frozen snapshot `p0-v1` containing real NCBI PubMed, Europe PMC, RxNorm, and openFDA normalized records.
- **Statistical Rigor:** Wilcoxon signed-rank testing, Cohen's $d_z$, and 1000-resample bootstrap 95% confidence intervals are computed from case-level deltas.

## 3. Scope & Limitations
- **Mock Generation Scope:** Deterministic mock generation isolates retrieval, trust scoring, and eligibility effects. It does not measure live LLM token distributions or generative hallucinations.
- **Next Step:** Proceed to `F0/F1-LIVE` using live LLM provider backends for generative answer quality benchmarking.