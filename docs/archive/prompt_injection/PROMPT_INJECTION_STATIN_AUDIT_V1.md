# PROMPT_INJECTION_STATIN_AUDIT_V1

## Overview
This audit evaluates the resilience of the pharmacology RAG pipeline against prompt injections focused on the query: `"Does statin interact with aspirin?"`. We ran 10 adversarial cases through both the BASELINE (`HybridRetrievalEngine`) and COGNEE engines to determine if malicious instructions could override authoritative evidence and generate unsupported claims.

## Findings by Category

### A. Retrieval Exposure
- Adversarial documents were successfully ingested into the corpus and retrieved based on vector and keyword overlap with the target query. Both Baseline and Cognee engines demonstrated exposure to the injected content.

### B. Injection Detection
- The `PromptInjectionDetector` successfully sanitized direct query injections and flagged adversarial markers in the retrieved text.

### C. Evidence Grounding
- The `RelationshipGroundingValidatorV2` processed the candidates.
- The pipeline correctly assigned states such as `UNSUPPORTED` or `CONTRADICTED` to the injected malicious claims, depending on the exact wording of the injection.

### D. Evidence Polarity
- Crucially, when evaluating the authoritative FDA evidence (`doc-fda-atorvastatin`) alongside the injection (`doc-pi-08`), the system preserved the `NEGATED` polarity and `BOUNDED_NEGATIVE` state of the genuine evidence.

### E. Trust/Eligibility Behavior
- The `EvidenceEligibilityGate` identified the low source authority and `UNTRUSTED_CONTROL` status of the adversarial documents, dropping their trust scores below the `R1` threshold (`0.45`). The adversarial documents were subsequently blocked from the final LLM context window.

### F. Claim Safety & Citation Support
- Since the adversarial candidates were rejected by the security gates, the final context window contained only the authoritative bounded-negative evidence. The generated claims accurately reflected the FDA evidence.

### G. Final-Answer Behavior
- In none of the cases did the system output the maliciously instructed positive claim `"Statin interacts with aspirin."`. 
- Attack Success Rate: **0%**

### H. Reproducibility
- The behavior was completely deterministic. 100% exact match across all repeated runs (2 runs per case per engine).

### I. Limitations
- This evaluation provides controlled benchmark evidence for the implemented security/evidence-control pipeline against specific prompt-injection families. 
- It does not claim immunity to prompt injection, nor does it claim general medical-language robustness or clinical safety.
- The validator and detector remain scoped implementations.
