# V3.1-HUMAN Annotation Guide

## Objective
Judge whether a candidate document provides clinical evidence that directly answers the query.

## Instructions
1. **Blinding**: You are evaluating document texts independent of how any search engine scored them. Do not assume a document is relevant just because it was suggested as a candidate.
2. **Relevance Labels**:
   - `DIRECT_SUPPORT`: The document explicitly answers the question or establishes the claim. (Must provide `evidence_span`).
   - `PARTIAL_SUPPORT`: The document addresses the topic but is incomplete (e.g., states mechanism but not clinical implication). (Must provide `evidence_span`).
   - `NOT_RELEVANT`: The document is topically similar (e.g., mentions both drugs) but does not contain the specific evidence requested.
   - `NO_EVIDENCE`: If all candidates for a case are NOT_RELEVANT, mark one row with NO_EVIDENCE.
3. **Evidence Span**: For any positive label, you MUST copy the exact contiguous sentence(s) from the document that provide the support. Do not paraphrase.
4. **Specific Domain Rules**:
   - **DDI**: Require actual evidence of the interaction relationship, not just co-occurrence.
   - **ADE**: Require evidence linking the drug to the event, not just mention of both.
   - **Pharmacology**: Require the precise mechanistic answer (target, clearance, etc).
   - **Medication Safety**: Require direct support for the safety issue (dosing, contraindication).
5. **High-Risk Cases**: R3 cases require a higher standard of review. Ensure the evidence unambiguously supports the claim.

## Output
Fill in the `relevance`, `evidence_span`, `annotation_reason`, `authority_tier` (e.g., PEER_REVIEWED_PUBMED), `annotator_id`, `review_timestamp`, and `confidence` columns in the provided CSV.