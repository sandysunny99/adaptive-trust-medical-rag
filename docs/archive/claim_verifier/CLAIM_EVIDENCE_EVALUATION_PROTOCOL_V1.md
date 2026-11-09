# CLAIM_EVIDENCE_EVALUATION_PROTOCOL_V1

## 1. Overview
The Claim-Evidence Verification Evaluation tests the independent capability of the post-generation Answer Safety Gate to detect ungrounded, over-claimed, or contradicted statements, and verify citation integrity.

## 2. Experimental Setup
This evaluation targets the verifier component in isolation (Component-Level Verification). It is **decoupled** from the Retrieval Engine (Gate 5) and the Prompt-Injection evaluation. 

## 3. Supported vs. Limiting Factors in the Current Verifier
The audit reveals that the current `claim_verifier.py` uses heuristic word-overlap (`_alignment_score`) and regex pattern matching (`detect_contradictions`) rather than a full semantic Natural Language Inference (NLI) model. 
- **Limitation:** It cannot reliably detect over-generalization (CE-07), partial clause support (CE-06), or paraphrase mapping. 
- **Limitation:** The vocabulary of states is strictly binary (`is_grounded = True/False`) coupled with an independent `contradiction` boolean, lacking native support for `PARTIALLY_SUPPORTED` or `INSUFFICIENT_EVIDENCE`.

## 4. Execution Workflow
1. Execute the 10-case test matrix (`CLAIM_EVIDENCE_TEST_MATRIX_V1.json`) against `AnswerSafetyGate.verify()`.
2. Map the output `VerificationReport` to the standardized claim states.
3. Determine if the gate correctly triggered `ABSTAIN`, `RELEASE`, or `QUALIFY`.
4. Calculate component-level detection rates for unsupported claims and contradictions.

## 5. E2E Generation Requirement
An end-to-end (E2E) generation test evaluating how the verification gate protects the real LLM output is currently **BLOCKED** due to missing API credentials in the environment. Therefore, this protocol strictly covers the component-level evaluation using synthetic claim strings injected directly into the verifier.
