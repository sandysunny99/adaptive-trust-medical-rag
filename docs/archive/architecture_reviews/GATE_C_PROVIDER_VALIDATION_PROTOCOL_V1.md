# GATE C LIVE PROVIDER VALIDATION PROTOCOL

**Date:** 2026-10-03  
**Stage:** CONTROLLED SCIENTIFIC VALIDATION  
**Type:** PROVIDER-NEUTRAL EXECUTION PATH VALIDATION

## 1. Purpose
Verify the execution integrity of real LLM provider paths. Gate C must confirm:
- Correct credential loading from the runtime environment.
- Successful network request/response to the live endpoint.
- Correct execution of structured output schemas.
- Enforcement of timeout, retry, and rate-limiting policies.
- Accurate provider error classification (e.g., distinguishing a 429 from a Security Block).
- Preservation of the security boundary (ensure prompt injection/trust checks run *before* the request).

Gate C does **NOT** validate clinical safety, hallucination reduction, or scientific retrieval superiority.

## 2. Provider Candidates
The following provider adapters exist in the repository but remain unverified via live scientific execution:
1. **Groq** (Primary Candidate)
2. **Cloudflare**
3. **Hugging Face**
4. **FreeLLMAPI**

*Note: Gemini is NOT required for Gate C. Phase 15 remains a separate, frozen historical experiment.*

## 3. Execution Requirements
Before a live provider test is executed, the following must be true:
1. **Human Decision:** The human researcher has selected the target provider.
2. **Credential Present:** The specific required API key (e.g., `GROQ_API_KEY`) is in `os.environ`.
3. **Configuration Valid:** The model and endpoint match the adapter logic.
4. **Preflight Pass:** Security boundary and audit paths are active.

## 4. Test Structure (Provider Connectivity Check)
A successful test consists of sending a safe, non-malicious standard medical query through the full pipeline to verify the infrastructure, *not* to measure accuracy.

## 5. Security Invariant
A transport failure (e.g., 502 Bad Gateway) may trigger a configured failover. A **security failure** (e.g., Prompt Injection detected, or Trust Score below threshold) MUST halt the pipeline entirely and must NEVER trigger a failover to another provider to bypass the block.
