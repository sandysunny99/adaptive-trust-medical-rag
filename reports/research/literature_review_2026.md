# 2023–2026 Literature Review: Medical RAG, Trust Scoring & Security

## 1. Medical RAG & Hallucination Mitigation (2023–2026)

- **MIRAGE / MedRAG Benchmark (2024):** Demonstrated that conventional dense semantic RAG is prone to evidence misattribution and entity confusion in complex pharmacology queries.
- **Clinical RAG Conversational Drift (2026):** Showed that multi-turn clinical interactions accumulate conversational drift, leading to severe factual hallucinations if un-gated.

## 2. RAG Threat Model & Adversarial Security (2024–2026)

- **Indirect Prompt Injection in RAG (2025):** Highlighted that retrieved context documents can serve as Trojan horses, carrying hidden instructions that override system safety prompts.
- **Retrieval Poisoning & Provenance Deficits (2025):** Identified unweighted vector indexing as a major security gap where malicious or outdated documents corrupt downstream generation.

## 3. Position of Adaptive Trust-Aware RAG

Our platform addresses these literature gaps by implementing a dual-safety-gated architecture combining pre-generation evidence eligibility with post-generation claim verification and risk-tiered (R0-R3) controlled abstention.
