# CLAIM_VERIFIER_V1_VS_V2_COMPARISON

## Overview
This document serves as an ablation and component comparison between the heuristic `ClaimVerifierV1` and the semantic `ClaimVerifierV2`. It highlights functional differences based on the controlled test matrix.

## Key Differences

### 1. Paraphrase Handling
- **V1 (Heuristic):** Fails to align claims that are heavily paraphrased. It relies on Jaccard overlap of words >= 4 characters. If synonyms are used, `_alignment_score` drops below `0.70` and the claim is incorrectly marked ungrounded.
- **V2 (Semantic):** Successfully aligns paraphrased claims using the underlying NLI semantic embeddings (`PubMedBERT-MNLI-MedNLI`), properly mapping them to `SUPPORTED` regardless of exact vocabulary overlap.

### 2. Contradiction Detection
- **V1 (Heuristic):** Relies entirely on a small list of absolute pattern regexes (`_NEGATION_SEEDS`) coupled with positive word matching. It fails to detect nuanced contradictions that do not match the exact pattern.
- **V2 (Semantic):** Natively calculates a `contradiction` probability using the cross-encoder. It accurately detects contradictions such as a positive DDI claim tested against a bounded-negative evidence statement.

### 3. Bounded-Negative Evidence & Overclaims
- **V1 (Heuristic):** Often blindly matches words (e.g., "interaction") and fails to appreciate the boundary "clinically significant pharmacokinetic". It may mark an overgeneralized claim as grounded simply due to token overlap.
- **V2 (Semantic):** Preserves the scope correctly. When presented with the evidence *"No clinically significant pharmacokinetic interaction observed"* and the claim *"There is no interaction of any kind between statin and aspirin"*, the model's `entailment` score is low because the premise does not entail the broader hypothesis. The claim is appropriately flagged.

### 4. Mixed-Claim Handling
- **V1 (Heuristic):** If a single sentence contains both a supported and an unsupported clause, V1 assigns a single global alignment score. Often, the supported tokens carry the score above 0.70, erroneously validating the entire mixed claim.
- **V2 (Semantic):** By evaluating the exact semantic relation of the text pair, V2 correctly registers low entailment or high contradiction/neutrality when a hypothesis introduces an unsupported, dangerous secondary clause (e.g., "...and therefore the drugs are completely safe").

## Conclusion
`ClaimVerifierV2` demonstrates a vastly superior capability to accurately categorize the support states of generated pharmacological claims, fully resolving the limitations that crippled the heuristic implementation of V1.
