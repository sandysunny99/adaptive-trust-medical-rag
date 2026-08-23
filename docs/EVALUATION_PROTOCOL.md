# Evaluation Protocol & Factual Grounding Specification

## 1. Scope & Definitions

This document defines the formal evaluation methodology, claim extraction rules, support criteria, and statistical calculation standards for the Adaptive Trust-Aware Medical RAG research platform.

## 2. Claim Extraction & Verification Rules

1. **Claim Extraction:** Generated responses are parsed into atomic, factual assertions using sentence and clause boundaries.
2. **Claim Categories:**
   - **Supported Claim:** Factually supported by at least one eligible evidence chunk in the current session context.
   - **Unsupported Claim:** Assertion not found or not supported in the retrieved session context (classified as hallucination).
   - **Contradicted Claim:** Assertion directly conflicts with an authoritative evidence chunk.
   - **Uncertain Claim:** Assertion with ambiguous or partial evidence support.
3. **PMID & Citation Verification:**
   - Every citation tag (e.g., `PMID:34567890`) is checked against the set of retrieved chunk IDs.
   - Unmatched or fabricated citations are flagged as hallucinated and stripped by the Answer Safety Gate.

## 3. Metric Formulations

- **Faithfulness:**
  $$\text{Faithfulness} = \frac{\text{Number of Supported Claims}}{\text{Total Claims in Answer}}$$
- **Hallucination Rate:**
  $$\text{Hallucination Rate} = 1.0 - \text{Faithfulness}$$
- **Citation Precision:**
  $$\text{Citation Precision} = \frac{\text{Valid Citations Matching Context}}{\text{Total Citations in Answer}}$$
- **Citation Recall:**
  $$\text{Citation Recall} = \frac{\text{Cited Relevant Chunks}}{\text{Total Relevant Chunks in Context}}$$
- **F1-Abstain:**
  $$\text{F1-Abstain} = \frac{2 \cdot \text{Precision}_{\text{abstain}} \cdot \text{Recall}_{\text{abstain}}}{\text{Precision}_{\text{abstain}} + \text{Recall}_{\text{abstain}}}$$

## 4. Evaluator Configuration
- Evaluator Model: `gemini-2.5-flash`
- Temperature: `0.0` (deterministic)
- Bootstrap Resamples: $N = 1000$
- Statistical Test: Paired Welch $t$-test / Bootstrap paired difference ($p < 0.05$).
