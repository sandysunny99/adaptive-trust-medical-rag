---
name: rag-integrity-rules
description: RAG pipeline integrity rules for hybrid retrieval, adaptive trust scoring, citation verification, and hallucination reduction.
trigger: always_on
---

# RAG Pipeline Integrity Rules

## 1. Dual Safety Gates
- **Evidence Eligibility Gate (Pre-Generation):** Evaluates retrieved document chunks on source authority, entity match, freshness, and anti-poisoning before feeding into LLM context.
- **Answer Safety Gate (Post-Generation):** Deterministically parses claims in the generated answer, cross-references with retrieved chunks, and verifies citation mappings.

## 2. Citation Integrity
- Every factual medical claim must be linked to a specific citation ID in the retrieved context.
- Hallucinated PMIDs, DOIs, URLs, or nonexistent document excerpts are strictly prohibited.
- If a generated claim cannot be verified against the session evidence, it must be stripped or the answer rejected.

## 3. Contradiction Detection
- When retrieved sources provide conflicting findings (e.g., Study A states interaction is minor, Study B states contraindication), the contradiction must be highlighted explicitly in the response along with the authority and date of both sources.
