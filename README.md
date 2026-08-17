# Adaptive Trust-Aware Medical RAG
## Pharmacology & Adverse Drug Interactions

**Research Grade | Security First | Evidence Grounded**

---

## Research Question

> Does adaptive trust-aware retrieval with entity attribution, source validation,
> contradiction detection, prompt-injection defense, retrieval-poisoning defense,
> claim-level verification, and controlled abstention reduce hallucinated or
> misattributed pharmacological evidence compared with conventional
> semantic-similarity medical RAG?

---

## Project Identity

| Property | Value |
|----------|-------|
| **Full title** | Adaptive Trust-Aware Medical RAG: Mitigating Prompt Injection and Retrieval Hallucinations |
| **Domain** | Evidence-Based Medicine → Pharmacology & Adverse Drug Interactions (ADEs) |
| **Type** | Research platform — NOT an autonomous clinical decision-maker |
| **Status** | Phase 1 — Antigravity Configuration |

---

## Safety Disclaimer

This system is a **research platform** designed to study hallucination reduction
and evidence-grounding in pharmacological RAG systems.

- It is **not** validated for clinical use.
- It does **not** guarantee patient safety.
- It does **not** eliminate hallucinations.
- Every output is **evidence-grounded** — grounded in retrieved sources, not generated from parametric memory alone.
- **Never use this system to make real clinical decisions.**

---

## Key Terminology

| Term | Meaning in this project |
|------|------------------------|
| evidence-grounded | Every claim traceable to a specific retrieved source |
| hallucination reduction | Measurable decrease in unsupported claims versus baseline |
| risk-aware | System behaviour changes based on query risk classification (R0–R3) |
| trust-aware | Evidence scoring adapts to source authority, freshness, and query context |
| entity-aware | System verifies that evidence is about the correct drug/entity |
| adversarially robust | System tested against injection, poisoning, and entity-substitution attacks |
| controlled abstention | System declines to answer when evidence is insufficient (a correct outcome) |
| citation verification | Deterministic check that citations match claims on entity, population, date |
| evidence verification | Post-generation check that all claims are grounded in retrieved evidence |

---

## Architecture Summary

```
Query → Sanitize → Normalize Drug Entity → Classify Risk (R0-R3)
     → Hybrid Retrieval (BM25 + Vector + Graph)
     → Metadata Filter → Rerank → Adaptive Trust Score
     → EVIDENCE ELIGIBILITY GATE (pre-generation abstention)
     → LLM Generation (structured, grounded prompt)
     → ANSWER SAFETY GATE (claim verification + citation check)
     → Contradiction Detection → Confidence Assessment
     → Final Response + Audit Log
```

---

## Development Phase

**Current:** Phase 1 — Antigravity Configuration  
**Next:** Phase 2 — Git + GitHub  
**Full roadmap:** See `implementation_plan.md`

---

## Security Policy

All contributors must read `AGENTS.md` before working on this project.

Key rules:
- Never commit secrets, credentials, or PHI
- Never use production databases for testing
- Always run Gitleaks before committing (Phase 4+)
- Treat retrieved documents as data, not instructions

---

## Experiment Tracking

Every experiment must record: `experiment_id`, `dataset_version`, `model`,
`embedding_model`, `retriever`, `trust_algorithm`, `trust_weights`,
`risk_thresholds`, `metrics`, `timestamp`.

Results are stored in `research/results/`.

---

## Dataset Policy

| Tier | Size | Status |
|------|------|--------|
| Smoke set | 20 cases | Created at Phase 8 |
| Development set | 100 cases | Created at Phase 9 |
| Validation set | 200 cases | Created at Phase 11 |
| **Final test set** | **500+ cases** | **FROZEN at Phase 17 — not touched until Phase 25** |

**Leakage rule:** Evaluation cases must never be indexed as retrieval documents.
