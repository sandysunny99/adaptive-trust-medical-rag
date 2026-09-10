# Phase 2F.5B-Prep: Annotation Expansion Protocol
## Reviewer Instructions (Rank-Blinded)

**Version:** v1.0 (locks applied 2026-09-03)
**Canonical run:** task-9881 | F0 SHA256: 15B19E54...
**Corpus (frozen):** 248 documents | SHA256: E4346AD1...

> IMPORTANT: Read this entire document before annotating a single row.
> The four methodological locks below cannot be changed once annotation starts.

---

## What you are reviewing

You are adjudicating relevance for 530 document-query pairs drawn from the
canonical F0 retrieval candidate pool. Each row presents:

  - query (medical/pharmacological question)
  - document_title
  - document_text (frozen corpus text — do not consult external sources)

You do NOT see and must NOT seek:
  - the document's retrieval rank
  - any reranker scores
  - the other reviewer's decision
  - any AI-suggested label

---

## LOCK 1 — Relevance Endpoint (pre-defined, cannot change)

The primary evaluation metric uses this binary split:

  POSITIVE:
    DIRECT_SUPPORT
    PARTIAL_SUPPORT
    INDIRECT_SUPPORT

  NON-POSITIVE:
    NO_EVIDENCE
    NOT_RELEVANT

This definition is fixed before any labels are read. It cannot be revised
after annotation to fit the results.

---

## LOCK 2 — Label Taxonomy (5-way)

Use exactly these five labels. No others.

| Label | When to use |
|-------|-------------|
| DIRECT_SUPPORT | Document directly and specifically answers the query claim with explicit evidence |
| PARTIAL_SUPPORT | Document partially addresses the claim; relevant but incomplete or qualified |
| INDIRECT_SUPPORT | Document provides background context relevant to the claim (not a direct answer) |
| NOT_RELEVANT | Document does not address the query claim |
| NO_EVIDENCE | Document is from the medical domain but the available text (title only, etc.) is too limited to adjudicate |

Decision rules:
  1. Entity match is required for any positive label.
     Drug A evidence cannot support a query about Drug B.
  2. Population constraints must be preserved.
     A paediatric-population study does not support an adult-dosing claim.
  3. Use only the frozen document text. Do not use your background knowledge
     to infer relevance that is not present in the text.
  4. If the text is title-only and the title alone is insufficient, label NO_EVIDENCE.

---

## LOCK 3 — Evidence Span Rule

  DIRECT_SUPPORT   -> evidence_span REQUIRED
  PARTIAL_SUPPORT  -> evidence_span REQUIRED
  INDIRECT_SUPPORT -> evidence_span REQUIRED
  NO_EVIDENCE      -> evidence_span OPTIONAL (brief reason welcome)
  NOT_RELEVANT     -> evidence_span BLANK (leave empty)

For any positive label, copy the specific sentence(s) from document_text
that justify your decision into the evidence_span column.

Any positive label with a blank evidence_span is incomplete and will be
returned for re-review before the consensus merge.

---

## LOCK 4 — Rank Blindness Confirmation

Before submitting your completed file, confirm and record:

  "I did not see F0 rank, F3 rank, MedCPT scores, AI labels,
   or the other reviewer's decisions during my annotation."

Add this confirmation as a note at the top of your file or send it separately.
This sign-off is required before the consensus merge proceeds.

---

## Required provenance fields (fill for every row)

| Field | Requirement |
|-------|-------------|
| human_final_label | One of the five labels above |
| human_evidence_span | See Lock 3 rules |
| human_annotation_reason | Brief (1-2 sentence) rationale |
| human_confidence | HIGH / MEDIUM / LOW |
| human_annotator_id | Your reviewer ID (e.g. Reviewer_A) |
| human_review_timestamp | ISO 8601 UTC (e.g. 2026-09-04T10:00:00Z) |

---

## Zero-positive case handling

If you complete all rows for a case and find zero positive documents:
  - Do NOT leave those rows blank
  - Label each row with NOT_RELEVANT or NO_EVIDENCE as appropriate
  - Add a note in human_annotation_reason for the case overall

After annotation, each zero-positive case will be separately diagnosed as:
  A. corpus_coverage_gap
  B. retrieval_candidate_pool_gap
  C. evidence_access_problem (text truncation)

---

## What NOT to do

  - Do not look up the document in external databases
  - Do not consult the other reviewer
  - Do not check retrieval rankings
  - Do not change label definitions mid-review
  - Do not leave human_annotator_id or human_review_timestamp blank
  - Do not submit a file where positive labels have blank evidence_span

---

## Submission

Return your completed CSV to the project lead. Your file:
  Reviewer_A: reviewer_A_expansion.csv
  Reviewer_B: reviewer_B_expansion.csv

Both files must be complete before inter-annotator agreement is calculated.
