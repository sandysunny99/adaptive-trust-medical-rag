# Phase 2F.5B-Prep Annotation Completion Protocol
## Controlled Annotation Completion, Issue Resolution, and Forward-Move Protocol

**Version:** v1.0
**Locked:** 2026-09-03
**Status:** AWAITING REVIEWER CSV SUBMISSION

> This document encodes the exact processing rules that apply when both reviewer
> CSVs are received. It must not be modified after annotation begins.
> Any deviation from this protocol is a blocking methodological issue.

---

## Project State at Protocol Lock

```
Phase 2F.5A-REAL-REPRODUCED   COMPLETE
Phase 2F.5A Diagnostic        COMPLETE
Phase 2F.5B-Prep              COMPLETE
Phase 2F.5B Annotation        PENDING
Phase 2F.5B Confirmation      LOCKED
Phase 2G Production           LOCKED
```

## Frozen Artifact SHA-256 Values (must be verified before gate passes)

```
runner_real_hardened.py   774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
f0_results.jsonl          15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
f3_results.jsonl          45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
debug_records.jsonl       6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
documents.json (corpus)   E4346AD15EC1F74AF9ECC010EF822503EB44638F1020E7F0FCB51AD5C58F42F7
```

---

## Processing Pipeline (in order — do not skip any step)

```
RECEIVE REVIEWER FILES
        |
INPUT / SCHEMA VALIDATION
        |
COVERAGE VALIDATION
        |
PROVENANCE VALIDATION
        |
RANK-BLINDNESS VALIDATION
        |
LABEL-TAXONOMY VALIDATION
        |
EVIDENCE-SPAN VALIDATION
        |
BINARY + 5-CLASS IAA
        |
DISAGREEMENT IDENTIFICATION
        |
ADJUDICATION (human only)
        |
CONSENSUS LABELS
        |
ZERO-POSITIVE CASE DIAGNOSIS
        |
CANONICAL RETRIEVAL / CORPUS HASH RECHECK
        |
PHASE 2F.5B GATE REPORT
        |
ONLY IF ALL GATES PASS: PHASE 2F.5B UNLOCK
```

---

## RULE 1 — Preserve original reviewer files

Immediately on receipt, copy originals to:

  submissions/reviewer_A_original.csv
  submissions/reviewer_B_original.csv

Record for each:
  submission_timestamp, file_size, sha256, row_count, column_count, annotator_id

Do not alter archived originals. Any normalization operates on copies only.

---

## RULE 2 — Verify exact expected coverage

Expected expansion rows per reviewer: 530
Expected case distribution:
  v3.1h-001: 50, v3.1h-002: 52, v3.1h-021: 51, v3.1h-022: 53, v3.1h-023: 53
  v3.1h-046: 51, v3.1h-047: 53, v3.1h-066: 54, v3.1h-067: 56, v3.1h-069: 57

Check per reviewer:
  - exactly 530 expansion rows
  - no missing case IDs
  - no unknown case IDs
  - no unknown document IDs
  - no duplicate (case_id, document_id) pairs
  - every row belongs to the canonical F0 pool

FAIL condition: any count differs from expected -> COVERAGE_GATE = FAIL
Action on fail: investigate discrepancy; do not silently add or remove rows.

---

## RULE 3 — Verify reviewer independence

Check:
  - same row universe (identical case_id / document_id sets)
  - independent labels (not copied)
  - independent rationale
  - independent evidence spans
  - independent timestamps

Flag if:
  - identical decision columns across suspiciously large portions
  - identical evidence spans verbatim
  - identical rationales
  - identical timestamps

Do not automatically conclude misconduct — record for review.
FAIL condition: independence cannot be established -> IAA_INDEPENDENCE_GATE = FAIL

---

## RULE 4 — Validate the five labels

Allowed values (exact, case-sensitive):
  DIRECT_SUPPORT, PARTIAL_SUPPORT, INDIRECT_SUPPORT, NO_EVIDENCE, NOT_RELEVANT

Any other value is invalid.
Do not silently map invalid labels. Document and get approval before any mapping.

---

## RULE 5 — Validate the pre-registered binary endpoint

LOCKED binary split (cannot be changed after annotation started):
  POSITIVE    = DIRECT_SUPPORT | PARTIAL_SUPPORT | INDIRECT_SUPPORT
  NON_POSITIVE = NO_EVIDENCE | NOT_RELEVANT

Calculate binary labels deterministically from five-class labels.
Do not allow endpoint redefinition based on observed results.

---

## RULE 6 — Validate evidence spans

  DIRECT_SUPPORT   -> evidence_span REQUIRED
  PARTIAL_SUPPORT  -> evidence_span REQUIRED
  INDIRECT_SUPPORT -> evidence_span REQUIRED
  NO_EVIDENCE      -> evidence_span OPTIONAL
  NOT_RELEVANT     -> evidence_span BLANK

Where technically possible, verify the span text occurs in document_text.
FAIL condition: any positive label has empty evidence_span -> POSITIVE_EVIDENCE_GATE = FAIL
Action: return flagged rows for re-review before consensus merge.

---

## RULE 7 — Validate provenance

Every row must contain non-empty values for:
  case_id, document_id, human_final_label, human_annotation_reason,
  human_confidence, human_annotator_id, human_review_timestamp

Timestamp: ISO 8601, UTC
Confidence: HIGH | MEDIUM | LOW

Any missing field -> PROVENANCE_GATE = FAIL
Do not fabricate timestamps. Do not substitute script execution time unless
explicitly authorized and documented as system-generated.

---

## RULE 8 — Verify rank blindness

Verify that reviewer-facing files did not expose:
  f0_rank, f3_rank, medcpt_score, AI label, other reviewer decision

These must remain backend-only in expansion_metadata.csv.
Do not expose backend metadata during IAA calculation.

Required annotator sign-off statement (per reviewer):
  "I did not see F0 rank, F3 rank, MedCPT scores, AI labels,
   or the other reviewer's decisions during my annotation."

FAIL condition: sign-off missing -> RANK_BLINDNESS = NOT_VERIFIED -> gate blocked.

---

## RULE 9 — Human reviewer data must remain primary

AI may be used ONLY for:
  schema checks, missing-field detection, exact-text span checking,
  duplicate detection, coverage accounting

AI must NOT:
  overwrite reviewer labels
  decide disagreements automatically
  determine consensus labels

Any substantive disagreement must be resolved by human adjudication.

---

## RULE 10 — Compute IAA before adjudication

Use the exact predefined overlap set. Do not remove disagreements selectively.

Calculate and report:
  N overlap positions
  binary agreement count
  binary disagreement count
  binary Cohen's kappa
  5-class agreement count
  5-class disagreement count
  5-class Cohen's kappa
  raw agreement percentage

Primary gate: BINARY_COHEN_KAPPA >= 0.60
FAIL condition: kappa < 0.60 -> IAA_GATE = FAIL
Do not manipulate the sample to increase kappa.

---

## RULE 11 — Identify every disagreement

Create: disagreement_queue.csv

Columns:
  case_id, document_id, query, document_title, document_text,
  reviewer_A_label, reviewer_B_label, reviewer_A_reason, reviewer_B_reason,
  reviewer_A_evidence_span, reviewer_B_evidence_span, adjudication_status,
  final_consensus_label, adjudication_reason, adjudicator_id, adjudication_timestamp

Do not expose retrieval metadata (f0_rank, f3_rank, medcpt_score) in this file.

---

## RULE 12 — Human adjudication

Every disagreement must be adjudicated using the frozen protocol:
  entity match, claim specificity, population constraints,
  available source text, evidence span, NO_EVIDENCE vs NOT_RELEVANT distinction

Do not resolve by majority vote with only two reviewers.
Use: third-party adjudication OR explicitly approved structured discussion.
Record final rationale for every adjudicated row.

---

## RULE 13 — Produce consensus labels

Create: consensus_labels.csv

Must contain exactly 600 positions:
  existing 70 canonical labels + 530 newly adjudicated expansion positions

For each of the 600 positions verify:
  case_id, document_id, final_consensus_label, evidence_span (where required),
  reason, confidence, provenance

Do not alter the original 70 labels unless a separate explicit adjudication
decision is documented and authorized.

---

## RULE 14 — Zero-positive case diagnosis

For each case with zero positive consensus labels, record:
  NO_POSITIVE_FOUND_IN_F0_POOL = YES

Then classify:
  A = corpus_coverage_gap
  B = retrieval_candidate_pool_gap
  C = evidence_access_problem

Do not add documents to corpus. Do not rerun retrieval.
Do not call a zero-positive case a retrieval failure without evidence.

---

## RULE 15 — Recheck frozen retrieval artifacts

Before unlocking Phase 2F.5B, independently verify SHA-256 of:
  runner_real_hardened.py, f0_results.jsonl, f3_results.jsonl,
  debug_records.jsonl, documents.json (corpus)

Must match values listed at top of this document.
FAIL condition: any hash differs -> RETRIEVAL_FREEZE_GATE = FAIL -> stop.

---

## RULE 16 — Verify no retrieval rerun occurred

Check task logs and filesystem provenance.
Confirm no retrieval runner was executed after annotation began.
Expected: RETRIEVAL_RERUN_DURING_ANNOTATION = NO
FAIL condition: rerun found -> PHASE_2F5B_GATE = FAIL -> investigate provenance impact.

---

## RULE 17 — Verify the final 600-position evaluation set

Must satisfy:
  600 / 600 positions
  10 / 10 cases
  60 positions per case
  0 duplicate case-document pairs
  0 missing canonical F0 positions

Calculate and report:
  DIRECT_SUPPORT count, PARTIAL_SUPPORT count, INDIRECT_SUPPORT count,
  NO_EVIDENCE count, NOT_RELEVANT count,
  binary positive count, binary non-positive count

---

## RULE 18 — F3 rank join timing

F3 ranks and MedCPT scores may be joined ONLY AFTER:
  consensus labels are finalized
  rank-blindness is verified
  annotation provenance is complete

Do not feed rank/score values backward into annotation decisions.

---

## RULE 19 — Phase 2F.5B gate report

Create: reports/phase2f5b/phase2f5b_annotation_gate_report.md

Include PASS / FAIL / NOT_VERIFIED for each gate with numerical evidence:
  COVERAGE, CONSENSUS_LABELS, BINARY_COHEN_KAPPA, 5_CLASS_COHEN_KAPPA,
  POSITIVE_EVIDENCE_SPANS_COMPLETE, ANNOTATOR_PROVENANCE_COMPLETE,
  RANK_BLINDNESS, RETRIEVAL_FREEZE, CORPUS_UNCHANGED,
  RETRIEVAL_RERUN_DURING_ANNOTATION, ZERO_POSITIVE_CASE_DIAGNOSIS

---

## RULE 20 — Gate decision logic

  PHASE_2F5B_READY = YES
  only if ALL of:
    coverage == 600
    consensus_labels == 600
    binary_kappa >= 0.60
    positive_evidence_spans_complete
    annotator_provenance_complete
    rank_blindness_verified
    retrieval_outputs_unchanged
    corpus_unchanged
    no_retrieval_rerun
    zero_positive_case_diagnosis_complete

  Otherwise: PHASE_2F5B_READY = NO

  5-class kappa must be REPORTED but does not gate the unlock.
  Binary kappa >= 0.60 is the locked primary gate.

---

## RULE 21 — Issue classification

NON-BLOCKING (resolve on copy, document):
  extra whitespace, encoding issues, CSV quoting, column order,
  case-insensitive formatting inconsistency

BLOCKING ANNOTATION ISSUE (stop and resolve):
  missing label, missing positive evidence span, missing provenance,
  rank exposure, reviewer dependence, invalid label, missing rows,
  duplicate rows, unresolved disagreement, kappa < 0.60

BLOCKING METHODOLOGICAL ISSUE (stop, incident report, await decision):
  retrieval rerun, corpus modification, F0/F3 modification,
  annotation leakage, changed relevance endpoint,
  changed label definitions after annotation began

---

## RULE 22 — Never carry an unresolved issue forward

Prohibited language:
  "mostly passed", "acceptable with minor issues", "we can fix this later",
  "proceed despite the discrepancy"

Every gate: PASS or FAIL. A failed gate means Phase 2F.5B remains locked.

---

## RULE 23 — If all gates pass

Update roadmap:
  Phase 2F.5A-REAL-REPRODUCED     COMPLETE
  Phase 2F.5A Diagnostic          COMPLETE
  Phase 2F.5B-Prep                COMPLETE
  Phase 2F.5B Annotation          COMPLETE
  Phase 2F.5B Readiness Gates     PASS
  Phase 2F.5B Confirmation        READY FOR EXPLICIT APPROVAL
  Phase 2G                        LOCKED

Do NOT automatically execute the confirmation experiment.
Explicit user approval is required before confirmation begins.

---

## RULE 24 — If any gate fails

Keep: Phase 2F.5B = LOCKED, Phase 2G = LOCKED

Create: reports/phase2f5b/phase2f5b_blocker_report.md
Include: FAILED_GATE, EVIDENCE, IMPACT, REQUIRED_CORRECTION, OWNER, STATUS

Then STOP.

---

## RULE 25 — Required final outputs

  experiments/annotations/v3_1_human/pilot/expansion_v1/submissions/
    reviewer_A_original.csv
    reviewer_B_original.csv
  experiments/annotations/v3_1_human/pilot/expansion_v1/
    disagreement_queue.csv
    consensus_labels.csv
    iaa_report.md
  reports/phase2f5b/
    phase2f5b_annotation_gate_report.md

Do not delete intermediate audit evidence.

---

## RULE 26 — Required final response format

  REVIEWER_A_RECEIVED = YES/NO
  REVIEWER_B_RECEIVED = YES/NO

  COVERAGE = PASS/FAIL (X/530 per reviewer)
  SCHEMA = PASS/FAIL
  LABEL_TAXONOMY = PASS/FAIL
  PROVENANCE = PASS/FAIL
  EVIDENCE_SPANS = PASS/FAIL
  RANK_BLINDNESS = PASS/FAIL / NOT_VERIFIED

  BINARY_COHEN_KAPPA = X
  BINARY_IAA_GATE = PASS/FAIL
  FIVE_CLASS_COHEN_KAPPA = X

  DISAGREEMENTS = X
  ADJUDICATED = X/X

  CONSENSUS_LABELS = X/600

  ZERO_POSITIVE_CASES = X
  ZERO_POSITIVE_DIAGNOSIS = X/10

  F0_SHA256 = 15B19E54...
  F3_SHA256 = 45E54B61...
  DEBUG_SHA256 = 6CBD595A...
  CORPUS_SHA256 = E4346AD1...

  RETRIEVAL_FREEZE = PASS/FAIL
  CORPUS_UNCHANGED = PASS/FAIL
  RETRIEVAL_RERUN_DURING_ANNOTATION = YES/NO

  PHASE_2F5B_READY = YES/NO
  PHASE_2F5B_STATUS = LOCKED/READY
  PHASE_2G_STATUS = LOCKED

  BLOCKERS = NONE / [list]

Do not report PHASE_2F5B_READY = YES unless every mandatory gate actually passes.

---

## Current stop condition

Until both reviewer CSVs are received and every gate above passes:
  NO CODE CHANGES
  NO RETRIEVAL RUN
  NO F0/F3 MODIFICATION
  NO CORPUS MODIFICATION
  NO CONFIRMATION TEST
  NO PRODUCTION INTEGRATION
