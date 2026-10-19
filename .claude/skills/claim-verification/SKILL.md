---
name: claim-verification
description: Post-generation verification workflows, claim extraction, NLI contradiction detection, citation verification, and answer safety gating.
---

# Claim Verification & Answer Safety Gate Skill

This skill governs the post-generation verification pipeline that validates generated responses against retrieved session evidence before release.

## Verification Pipeline Stages

```
Generated Answer
   │
   ▼
[1] Atomic Claim Decomposition (spaCy / rule-based claim extractor)
   ├── Split answer into discrete, verifiable factual propositions
   │
   ▼
[2] Claim-to-Evidence Alignment Check
   ├── Compute semantic & lexical alignment between proposition and retrieved chunks
   ├── Flag any claim without supporting retrieved evidence chunk (Score < 0.70)
   │
   ▼
[3] Citation Integrity & Entity Check
   ├── Verify citation ID [Source X] exists in the retrieved evidence list
   ├── Verify that the referenced document actually supports the specific claim
   ├── Verify the entity (Drug name, dosage, population) matches the claim exactly
   │
   ▼
[4] Contradiction & Negation Detection
   ├── Run NLI model (Entailment / Neutral / Contradiction) against retrieved evidence
   ├── Detect internal contradictions or unsupported absolute claims ("100% safe", "never causes")
   │
   ▼
[5] Answer Safety Gate Decision
   ├── ALL Claims Grounded & Validated → Release Response + Confidence Score
   ├── Minor Ungrounded Non-Critical Claims → Strip / Qualify claims and re-evaluate
   └── Critical Safety Claim Ungrounded / Contradiction → ABSTAIN with explanation
```

## Confidence Assessment Formula

$$\text{Confidence} = \alpha \cdot \text{GroundingRatio} + \beta \cdot \text{MeanCitationTrust} + \gamma \cdot (1 - \text{ContradictionScore})$$

Where $\alpha = 0.4$, $\beta = 0.4$, $\gamma = 0.2$. Responses with Confidence below threshold for the query risk tier are rejected.
