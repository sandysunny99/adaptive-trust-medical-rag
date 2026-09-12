# Variant Effect Matrix (GATE 5)

This matrix defines the precise intended experimental treatment for each pairwise comparison in the ablation study. 
Do not refer to all differences generically as "the security effect." 

## B ? D Comparison
* **CONTROL CONDITION**: Variant B (Baseline Semantic/Hybrid RAG)
* **TREATMENT CONDITION**: Variant D
* **WHAT CHANGES**: The normalized drug entities (query_drugs) are explicitly injected into the prompt prefix.
* **WHAT REMAINS IDENTICAL**: Corpus, Top-K, Retrieval pipeline, Context length.
* **ESTIMATED EFFECT**: Effect of explicit entity-awareness in the prompt on the LLM's adherence to the correct drug.

## B ? E Comparison
* **CONTROL CONDITION**: Variant B (Baseline Semantic/Hybrid RAG)
* **TREATMENT CONDITION**: Variant E
* **WHAT CHANGES**: AdaptiveTrustScorer is applied to candidates. Only candidates with trust scores = the risk-tier threshold (e.g., 0.45) are included in the prompt context.
* **WHAT REMAINS IDENTICAL**: Retrieval engine outputs.
* **ESTIMATED EFFECT**: Effect of adaptive trust-aware pre-generation evidence gating on hallucination and misattribution rates.

## B ? F Comparison
* **CONTROL CONDITION**: Variant B (Baseline Semantic/Hybrid RAG)
* **TREATMENT CONDITION**: Variant F (Full Architecture)
* **WHAT CHANGES**: Application of the full AdaptiveTrustRAGOrchestrator, including:
  - Input query sanitization
  - Prompt injection detection
  - Trust-aware evidence gating (Eligibility Gate)
  - Answer verification (Answer Safety Gate / NLI)
  - Controlled abstention (if gates fail)
* **WHAT REMAINS IDENTICAL**: Underlying retrieval engine and raw candidate lists.
* **ESTIMATED EFFECT**: Effect of the full dual-gate security and verification architecture on end-to-end safety and abstention rates.

## D ? E Comparison
* **CONTROL CONDITION**: Variant D (Entity Prompting)
* **TREATMENT CONDITION**: Variant E (Trust Gating)
* **WHAT CHANGES**: Pre-generation evidence filtering based on authority, freshness, and entity-match.
* **WHAT REMAINS IDENTICAL**: Both normalize entities.
* **ESTIMATED EFFECT**: Value of actively filtering evidence vs passively prompting the LLM with entities.

## E ? F Comparison
* **CONTROL CONDITION**: Variant E (Trust Gating Only)
* **TREATMENT CONDITION**: Variant F (Full Architecture)
* **WHAT CHANGES**: Addition of post-generation verification, NLI contradiction checks, and input/retrieval poisoning defense.
* **WHAT REMAINS IDENTICAL**: Pre-generation trust filtering.
* **ESTIMATED EFFECT**: Marginal benefit of post-generation verification and injection/poisoning defenses over trust-filtering alone.
