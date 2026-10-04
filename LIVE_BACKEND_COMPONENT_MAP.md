# Live Backend Component Map

This document maps the validated research components to their live application equivalents, ensuring safe reuse without entangling the research state.

## 1. Input Sanitization
**Component:** `adaptive_trust_medical_rag.security.sanitizer.sanitize_query`
**Live Usage:** Applied independently to each drug name in the `AnalyzeRequest`.
**Safety Note:** Prevents cross-site scripting and obvious prompt injections before hitting the normalizer.

## 2. Prompt Injection Detection
**Component:** `adaptive_trust_medical_rag.security_extensions.injection_detector.PromptInjectionDetector`
**Live Usage:** Inspects the sanitized drug names and blocks execution if malicious patterns are detected. Returns a `SecurityDecision`.

## 3. Drug Entity Normalization
**Component:** `adaptive_trust_medical_rag.normalization.drug_normalizer.DrugNormalizer`
**Live Usage:** Uses `normalize_batch()` to concurrently resolve RxCUIs for all provided drug names. Returns `DrugEntity` objects.
**Safety Note:** Ensures the live app uses canonical RxNorm identifiers for evidence retrieval, avoiding brand-name confusion.

## 4. Hybrid Retrieval
**Component:** `adaptive_trust_medical_rag.retrieval.hybrid_retrieval.HybridRetrievalEngine`
**Live Usage:** Queries the exact same retrieval engine used in research (BM25 + Vector + Graph).
**Safety Note:** Currently loaded with a minimal dummy corpus in `app.py` for end-to-end testing, but the component is fully production-ready.

## 5. Retrieval Poisoning Detection
**Component:** `adaptive_trust_medical_rag.security_extensions.poisoning_detector.RetrievalPoisoningDetector`
**Live Usage:** Verifies the cryptographic hashes and provenance signatures of all retrieved evidence chunks. Chunks failing this check (or with high `poisoning_score`) are discarded.

## 6. Adaptive Trust Scoring
**Component:** `adaptive_trust_medical_rag.trust_scoring.trust_scorer.AdaptiveTrustScorer`
**Live Usage:** Calculates trust factors (authority, entity match, freshness, consistency) and evaluates them against the query's dynamic risk tier (R0-R3).

## 7. Pre-LLM Evidence Eligibility (Controlled Abstention)
**Component:** Custom implementation within `LiveMedicalRAGService`
**Live Usage:** Rejects candidates below the risk tier's trust threshold. If no chunks pass, triggers a controlled abstention *before* calling the LLM, saving compute and enforcing safety.

## 8. LLM Generation
**Component:** `adaptive_trust_medical_rag.llm_backend.groq_backend.GroqBackend`
**Live Usage:** Receives a specific prompt (`LIVE_APP_PROMPT_V1`) instructing it to output structured JSON conforming to the `AnalyzeResponse` components.

## 9. Claim Verification & Post-LLM Safety
**Component:** `adaptive_trust_medical_rag.verification.claim_verifier_v2.ClaimVerifierV2`
**Live Usage:** Verifies the `claims_for_verification` outputted by the LLM against the retrieved evidence chunks. If claims are unsupported or contradicted, the pipeline triggers a post-generation abstention.

## Summary of Integration
The `LiveMedicalRAGService` cleanly separates these components from the FastAPI HTTP layer. It streams server-sent events (SSE) back to the client at each stage, transforming backend execution state into real-time UI updates.
