---
name: medical-rag-evaluation
description: Experimental evaluation protocols, RAGAS/DeepEval benchmarking, ablation design, leakage prevention, and statistical reporting.
---

# Medical RAG Evaluation Skill

This skill defines the evaluation methodology, metrics definitions, benchmark datasets, and statistical rigor required for research-grade validation.

## Benchmark Datasets & Partitioning

| Tier | Size | Usage Policy | Leakage Controls |
|------|------|--------------|------------------|
| **Smoke Set** | 20 cases | CI / Quick sanity smoke tests | Non-overlapping with test |
| **Development Set** | 100 cases | Active debugging & prompt tuning | Non-overlapping with test |
| **Validation Set** | 200 cases | Trust weight and threshold tuning | Non-overlapping with test |
| **Final Test Set** | **500+ cases** | **FROZEN — Evaluated only once at Phase 25** | Strictly held out; startup verification blocks if indexed |

## Core Evaluation Metrics

1. **Hallucination Rate:** Proportion of generated factual claims not supported by evidence.
2. **Faithfulness / Groundedness:** (RAGAS / DeepEval) fraction of claims inferable from context.
3. **Citation Precision & Recall:** Accuracy of attributed citations to correct source documents.
4. **Entity Attribution Accuracy:** Proportion of claims correctly mapped to the queried drug entity.
5. **Abstention Appropriateness (F1-Abstain):** Precision and recall of abstentions on unanswerable/poisoned queries.
6. **Robustness to Prompt Injection:** Attack success rate (ASR) against direct and indirect injection vectors.
7. **Retrieval Poisoning Resistance:** System integrity when poisoned documents are introduced into retrieval corpus.

## Ablation Study Matrix

Evaluate system variations to quantify the marginal impact of each security and trust component:
- **Baseline A:** Vanilla LLM (Direct prompting without retrieval)
- **Baseline B:** Standard Semantic RAG (Dense vector only, no trust engine, no gates)
- **Ablation C:** BM25 + Vector Hybrid Retrieval (No trust scoring)
- **Ablation D:** Hybrid + Adaptive Trust Scoring (Pre-generation gate active)
- **Ablation E:** Full Pipeline without Post-Generation Answer Safety Gate
- **Full Architecture (F):** End-to-end Trust-Aware Medical RAG with Dual Gates and Entity Attribution.

## Statistical Rigor Requirements

- Report all metrics with 95% Confidence Intervals calculated via bootstrap resampling ($N = 1,000$).
- Conduct paired t-tests or Wilcoxon signed-rank tests for comparing system variations against baseline.
- Record complete parameter sets (`model`, `temperature`, `trust_weights`, `dataset_version`, `timestamp`) in MLflow.
