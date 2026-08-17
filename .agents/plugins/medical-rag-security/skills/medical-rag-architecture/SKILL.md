---
name: medical-rag-architecture
description: Overview and reference for the end-to-end Adaptive Trust-Aware Medical RAG pipeline, dual gates, risk tiers, and system components.
---

# Medical RAG Architecture Reference

This skill guides the design, implementation, and maintenance of the complete pipeline.

## End-to-End Architecture Flow

```
1. Query Input
   ↓
2. Input Sanitization & Prompt Injection Defense (Regex + heuristic)
   ↓
3. Drug Entity Normalization (RxNorm API / scispaCy → RxCUI / DrugBank ID)
   ↓
4. Query Risk Classification (Tier R0 to R3)
   ↓
5. Hybrid Retrieval (BM25 + Dense Vector pgvector + Graph Candidates Neo4j)
   ↓
6. Metadata Filtering & Reciprocal Rank Fusion (RRF)
   ↓
7. Cross-Encoder Reranking (sentence-transformers)
   ↓
8. Adaptive Trust Scoring (Authority, Freshness, Entity Match, Consistency, Anti-Poisoning)
   ↓
9. [PRE-GENERATION] EVIDENCE ELIGIBILITY GATE
   ├── Pass → Proceed to LLM Generation
   └── Fail → Trigger Structured Abstention Response
   ↓
10. Grounded LLM Generation (Structured Prompt with Session Evidence Context)
   ↓
11. [POST-GENERATION] ANSWER SAFETY GATE
   ├── Claim Extraction & Grounding Verification
   ├── Deterministic Citation Matching
   ├── Contradiction Detection (NLI + Heuristics)
   └── Confidence Assessment
   ↓
12. Final Answer Formatting & Structured Audit Logging (PostgreSQL `audit_events`)
```

## Risk Classification Tiers

- **R0 (Informational / General):** Mechanism of action, drug class, basic pharmacology. Trust threshold: `0.30`.
- **R1 (Standard Clinical Guidance):** Standard dosing, common side effects, mild warnings. Trust threshold: `0.45`.
- **R2 (High Caution):** Black-box warnings, vulnerable populations (pediatric, pregnancy), off-label usage. Trust threshold: `0.60`.
- **R3 (Critical Safety / Contraindication):** Fatal drug-drug interactions, lethal toxicity, narrow therapeutic index. Trust threshold: `0.75`.
