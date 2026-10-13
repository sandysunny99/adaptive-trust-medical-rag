---
name: hybrid-retrieval
description: Execution patterns for BM25 keyword search, dense vector retrieval with pgvector, graph candidate expansion with Neo4j, and Reciprocal Rank Fusion.
---

# Hybrid Retrieval Skill

This skill governs the multi-channel retrieval strategy combining lexical, semantic, and structural knowledge.

## Retrieval Channels

1. **BM25 Lexical Retrieval (`rank_bm25` / PostgreSQL Full-Text Search):**
   - Focuses on exact entity mentions, trade names, drug dosages, and technical medical terms.
   - Mitigates vocabulary mismatch when specific chemical identifiers are queried.

2. **Dense Vector Retrieval (`pgvector` + `sentence-transformers`):**
   - Focuses on semantic intent, clinical context, mechanism of action, and symptomatic descriptions.
   - Cosine similarity on normalized dense vector embeddings.

3. **Knowledge Graph Traversal (`Neo4j` / Relational Graph Path):**
   - Retrieves direct drug-drug interaction edges, contraindication relationships, and shared metabolic pathways (e.g., CYP3A4 substrate/inhibitor interactions).

## Candidate Fusion: Reciprocal Rank Fusion (RRF)

Combine candidate lists from all active channels $C$:

$$\text{RRF\_Score}(d) = \sum_{c \in C} \frac{1}{k + \text{rank}_c(d)}$$

Where constant $k = 60$ (standard robust RRF constant).

## Re-ranking Pipeline

1. Select top $N = 50$ fused candidates from RRF.
2. Run cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` or medical cross-encoder) to score query-document interaction.
3. Apply SQL metadata filters (remove expired, retracted, or quarantined records).
4. Deliver top $K = 10$ candidates to Adaptive Trust Engine.
