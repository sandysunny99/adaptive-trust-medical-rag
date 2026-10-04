# CLAIM_VERIFIER_V2_SPEC

## Overview
This specification outlines the semantic contract for `ClaimVerifierV2`. Unlike V1, V2 will use a Natural Language Inference (NLI) model to assess semantic entailment between the generated claim and the retrieved evidence context.

## Semantic States & Mappings

### 1. NLI Raw Outputs
The underlying NLI model must produce probabilities or logits for three fundamental semantic relationships:
- `ENTAILMENT`: The evidence logically supports the claim.
- `CONTRADICTION`: The evidence logically opposes the claim.
- `NEUTRAL`: The evidence neither supports nor opposes the claim.

### 2. Supported State Output Vocabulary
Based on the raw NLI probabilities, V2 must map the results to the following robust state vocabulary:
- **`SUPPORTED`**: The claim is fully entailed by the evidence.
- **`PARTIALLY_SUPPORTED`**: The claim contains multiple clauses where some are entailed and others are neutral (requiring multi-claim decomposition).
- **`CONTRADICTED`**: The claim is contradicted by the evidence (e.g., claiming a positive DDI when the evidence explicitly denies one).
- **`UNSUPPORTED`**: The claim contains factual information completely absent from the evidence.
- **`INSUFFICIENT_EVIDENCE`**: The evidence is too sparse or vague to make a determination.
- **`AMBIGUOUS`**: The semantic relationship cannot be confidently resolved (e.g., conflicting NLI probabilities below threshold bounds).

## Mandatory Capabilities

### 1. Scope & Qualification Preservation
V2 must successfully handle bounded-negative statements without overgeneralizing. 
- Example Evidence: *"No clinically significant pharmacokinetic drug-drug interactions have been observed..."*
- Example Claim: *"Statin and aspirin are completely safe together."*
- Required State: **`UNSUPPORTED`** (or `CONTRADICTED`). The model must recognize that "completely safe" exceeds the scope of "no pharmacokinetic interactions".

### 2. Independent Verification
Each clause of a multi-clause sentence must be evaluated independently. V2 will not label an entire sentence `SUPPORTED` merely because one clause yields high entailment.

### 3. Citation Verification
V2 will accept citation markers (`[Source N]`). It will perform the semantic entailment check specifically against the referenced chunk ID. If the referenced chunk evaluates to `NEUTRAL` or `CONTRADICTED`, the state will be mapped to `CITATION_UNSUPPORTED`, even if another retrieved chunk theoretically supports the claim.

## Required Data Structures
- `AtomicClaim`: Claim text, parsed citations.
- `EvidenceSegment`: Text, source ID, chunk ID.
- `SemanticJudgment`: Extracted NLI scores (`entailment`, `contradiction`, `neutral`).
- `FinalSupportState`: The mapped state from the vocabulary above.
- `VerificationReport`: Final output aggregating all `SemanticJudgment` objects and yielding a `GateDecision` (`release`, `qualify`, `abstain`).
