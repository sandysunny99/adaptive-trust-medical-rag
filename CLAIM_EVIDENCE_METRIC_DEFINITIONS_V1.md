# CLAIM_EVIDENCE_METRIC_DEFINITIONS_V1

## Overview
These metrics evaluate the standalone performance of the Claim-Evidence Verification module. They are distinct from the retrieval metrics and from the final answer generation success.

## Component-Level Metrics

### 1. Claim Support Rate
- **Definition:** The percentage of correctly validated `SUPPORTED` claims.
- **Formula:** (True Positives for SUPPORTED) / (Total inherently supported claims tested)

### 2. Unsupported Claim Detection Rate
- **Definition:** The module's ability to flag claims that lack sufficient grounding in the retrieved context.
- **Formula:** (Successfully flagged unsupported claims) / (Total unsupported claims tested)

### 3. Contradiction Detection Rate
- **Definition:** The module's ability to detect when a generated claim directly opposes the retrieved evidence.
- **Formula:** (Successfully flagged contradictions) / (Total explicit contradictions tested)

### 4. Citation Support Rate
- **Definition:** The accuracy of verifying that a specific cited source (`[Source N]`) actually contains the supporting text for the claim.
- **Formula:** (Accurately verified/rejected citations) / (Total citations tested)

### 5. Overclaim Detection Rate
- **Definition:** The module's ability to detect bounded-negative generalizations (e.g., expanding "no pharmacokinetic interaction" to "no interaction at all").
- **Formula:** (Successfully flagged overclaims) / (Total overclaims tested)

### 6. Safe Abstention Rate
- **Definition:** The rate at which the `AnswerSafetyGate` successfully resolves to `GateDecision.abstain` when presented with critical ungrounded claims or contradictions.
- **Formula:** (Successful Abstentions) / (Total critical-risk ungrounded/contradicted test cases)

### 7. Claim-Level Reproducibility
- **Definition:** The percentage of test cases where repeated execution of the exact same claim + evidence string results in identical alignment scores, contradiction flags, and final gate decisions.
