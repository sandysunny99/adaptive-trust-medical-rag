# V3.1-HUMAN Pilot Annotation Instructions

## Purpose
The purpose of this pilot is to validate the annotation process, workflow, and instructions before annotating the full 80-case dataset.

## Workspace
- The 248-document frozen corpus is located at: `experiments/evidence_snapshots/retrieval-v3-real/documents.json`
- The review template is: `pilot_review.csv`

## Workflow
1. Open `pilot_review.csv`. You have 10 cases (2,480 rows total).
2. For each case, search the frozen corpus or the document_text column for evidence.
3. If evidence is found, mark the row as `DIRECT_SUPPORT` or `PARTIAL_SUPPORT`.
   - You MUST copy the exact contiguous `evidence_span` from the source text.
   - You MUST provide an `annotation_reason`.
   - Provide `confidence` (HIGH, MEDIUM, LOW), `annotator_id`, and `review_timestamp` (UTC ISO-8601).
4. For all other reviewed candidate documents that do not provide evidence, mark `NOT_RELEVANT`.
5. Only if you have searched the corpus and conclude there is no evidence available for the query, mark exactly one row for that case as `NO_EVIDENCE`.
6. Save your completed file in `completed/reviewer_A.csv`. Do NOT overwrite the blank `pilot_review.csv`.

## Rules
- DDI: Require actual interaction evidence (A affects B), not just co-occurrence.
- ADE: Require evidence connecting drug to adverse event. Respect negation (e.g., 'no association').
- Pharmacology: Match the exact requested concept (mechanism, clearance, etc.).
- Medication Safety: Match the exact safety question (renal dosing, etc.).
