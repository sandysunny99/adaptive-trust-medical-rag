# Research Evidence Classification

**Date:** 2026-08-30  
**Commit:** 4a704f5  

## Evidence Classification Rules

- **VERIFIED LIVE EXECUTION:** Real external API/system call with recorded response hash
- **ENGINEERING EXPERIMENT:** Real algorithmic execution on controlled data; no real LLM
- **SIMULATION:** Mock/stub generation; metrics are artefacts of mock, not real system
- **DOCUMENTATION ONLY:** Written report not backed by traceable execution
- **UNVERIFIED:** Cannot be traced from repository

## Classification Table

| Result | Source Artifact | Execution Type | Evidence Level | Allowed for Paper? | Notes |
|---|---|---|---|---|---|
| Canonical R1 single-case trace | reports/audit/canonical_r1_verification.md | Pipeline unit test | PARTIALLY VERIFIED | ⚠️ Limited | Single case; mock LLM; demonstrates orchestrator wiring only |
| 5-case live validation | reports/audit/five_case_validation.md | Mock pipeline | SIMULATION | ❌ NO | LiveModelAdapter template string |
| 20-case smoke run (live-smoke-v1) | experiments/runs/live-smoke-v1/ | execution_type: simulation | SIMULATION | ❌ NO | summary.json explicitly labels mock backend |
| P0 PubMed live connectivity | p0-v1/manifest.json (hashes) | VERIFIED LIVE HTTP | VERIFIED LIVE EXECUTION | ✅ YES (connectivity claim only) | 3 records; not comprehensive |
| P0 Europe PMC live connectivity | p0-v1/manifest.json (hashes) | VERIFIED LIVE HTTP | VERIFIED LIVE EXECUTION | ✅ YES (connectivity claim only) | 3 records |
| P0 RxNorm live connectivity | p0-v1/manifest.json | VERIFIED LIVE HTTP | VERIFIED LIVE EXECUTION | ✅ YES (connectivity claim only) | 4 drug lookups |
| P0 openFDA live connectivity | p0-v1/manifest.json | VERIFIED LIVE HTTP | VERIFIED LIVE EXECUTION | ✅ YES (connectivity claim only) | 4 label lookups |
| F0/F1-v1 all metrics | experiments/runs/f0-f1-v1/ | Hard-coded p0_boost=0.03 | SIMULATION — INVALID | ❌ NO | Forensically classified; never cite |
| F0/F1-DM Precision@5 (+0.37, p=0.0003) | experiments/runs/f0-f1-v2/summary.json | Real hybrid+trust retrieval | ENGINEERING EXPERIMENT | ✅ YES with caveats | Valid as retrieval experiment; cite as "controlled mock experiment" |
| F0/F1-DM Citation Precision (+0.19, p=0.006) | experiments/runs/f0-f1-v2/summary.json | Real retrieval+trust | ENGINEERING EXPERIMENT | ✅ YES with caveats | Valid for retrieval grounding claim |
| F0/F1-DM Faithfulness (-0.037) | experiments/runs/f0-f1-v2/summary.json | Mock template answer | SIMULATION | ❌ NO | Artefact of 160-char template; not LLM quality |
| F0/F1-DM Hallucination Rate (+0.037) | experiments/runs/f0-f1-v2/summary.json | Mock template answer | SIMULATION | ❌ NO | Same as above |
| Ablation A-F all metrics | Not yet run at publication scale | Mock | SIMULATION | ❌ NO | Must be re-run with real LLM |
| Trust weights (adaptive claim) | config/trust.yaml | Design specification | DOCUMENTATION ONLY | ⚠️ With accurate terminology | Not "adaptive ML" — specify "risk-stratified fixed-weight heuristic" |
| Attack success rate | None | Not measured | UNVERIFIED | ❌ NO | No adversarial evaluation exists |

## Claims Currently Supportable

1. The P0 adapters (PubMed, Europe PMC, RxNorm, openFDA) retrieve real biomedical evidence with verified provenance. ✅
2. Adding P0 evidence to the base corpus increases retrieval Precision@5 from 0.24 to 0.61 (p=0.0003, dz=1.33) under controlled deterministic-mock conditions with a 4-document base corpus. ✅ (with scope caveats)
3. The trust-scoring eligibility gate accepts/rejects evidence chunks based on a 9-factor weighted score derived from a risk-stratified configuration. ✅ (implementation claim)
4. The injection sanitizer detects and strips 25 known prompt injection patterns. ✅ (rule-based coverage claim)
5. The forensic auditor independently verifies SHA-256 response hashes without importing any production generator. ✅

## Claims NOT Currently Supportable

1. Any faithfulness or hallucination rate improvement — mock LLM only
2. Claim verification quality improvement — rule-based lexical alignment on template responses
3. Ablation A-F comparison — identical retrieval between B and C; mock LLM throughout
4. Security attack resistance — no adversarial evaluation conducted
5. Any medical claim quality improvement — requires real LLM + real clinical evaluation framework
