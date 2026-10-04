# PROMPT_INJECTION_V1_METHOD_AUDIT

**CURRENT_RESULT_CLASSIFICATION = COMPONENT_DIAGNOSTIC_NOT_E2E**

## Overview
The initial execution of the Prompt Injection Evaluation (V1) successfully demonstrated core component-level behaviors—such as the deterministic operation of the `PromptInjectionDetector`, `RelationshipGroundingValidatorV2`, and `EvidenceEligibilityGate` against adversarial documents structured as `UNTRUSTED_CONTROL`. 

However, the evaluation harness contained several methodological flaws that prevent it from qualifying as a valid, end-to-end (E2E) research evaluation. It is therefore reclassified as component/diagnostic evidence.

## Methodological Limitations Identified

### 1. Unauthorized Retrieval Configuration
The evaluation substituted the authorized `HybridRetrievalEngine` backed by the `S-PubMedBert-MS-MARCO` embedding model with a `SimpleEmbeddingModel` mock. This broke continuity with the frozen Gate 5 baseline and invalidated retrieval exposure metrics.

### 2. Mock LLM Backend
The script utilized a deterministic `MockLLM` that generated hardcoded responses based on string-matching in the prompt. This failed to demonstrate how an actual generative AI model responds to injected adversarial context. E2E prompt-injection evaluation fundamentally requires an actual LLM.

### 3. Circular Claim & Citation Verification
The metrics `claim_verification` and `citation_support` were strictly derived from the `attack_success` boolean flag, rather than relying on an independent post-generation verification component. 

### 4. Target Identifiers Exposed in Queries
Adversarial cases leaked explicit target identifiers (e.g., `doc-pi-02`) directly into the user query. This artificially skewed retrieval dynamics and did not represent a realistic scenario where an ordinary user query unknowingly retrieves a poisoned document.

### 5. Improper Multi-Document Test
Case PI-STATIN-10 was simulated by placing multi-document descriptions inside a single chunk, rather than genuinely testing the retrieval and ingestion of multiple, independent documents containing mixed benign/authoritative/malicious content.

### 6. Loose Injection Detection Measurement
The `injection_detected` metric was inferred through substring matching (`"BLOCK" in detail`) against free-text audit logs, rather than extracting structured `SecurityState` enums from the detector events.
