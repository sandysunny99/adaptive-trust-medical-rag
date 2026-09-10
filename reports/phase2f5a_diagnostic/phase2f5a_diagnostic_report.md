# Phase 2F.5A Diagnostic Report
## Adaptive Trust-Aware Medical RAG: Pilot Set Retrieval Diagnostic

**Canonical run:** task-9881
**Runner SHA256:** 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
**Execution timestamp (UTC):** 2026-09-03T14:43:31.102844Z
**Report generated:** 2026-09-03 IST

> RESEARCH DISCLAIMER: This software is a research testbed, not an FDA-approved
> clinical decision-making system. All outputs are evidence-grounded research results,
> not clinical advice.

> SCIENTIFIC FRAMING: These results represent DIAGNOSTIC EVIDENCE of retrieval and
> reranking behaviour on the 10-case AI-assisted pilot annotation set. The annotation
> set is not exhaustive independent ground truth. This is NOT a statistical confirmation
> that F3 outperforms F0.

---

## 1. Dataset Summary

| Item | Value |
|------|-------|
| Cases analysed | 10 |
| Total documents labelled across all cases | 98 |
| Positive documents (DIRECT/PARTIAL/INDIRECT_SUPPORT) | 2 |
| Negative documents (NOT_RELEVANT / NO_EVIDENCE) | 96 |
| F0 candidates per case | 60 (BM25 + S-PubMedBERT + Graph + RRF k=60) |
| F3 candidates per case | 60 (F0 pool re-ranked by ncbi/MedCPT-Cross-Encoder) |
| Frozen corpus size | 248 documents |
| Corpus SHA256 | E4346AD15EC1F74AF9ECC010EF822503EB44638F1020E7F0FCB51AD5C58F42F7 |

---

## 2. Per-Query Diagnostic Table

Columns: n_pos = positive docs in label set; hits@k = positive docs in top-k;
d@k = F3_hits@k - F0_hits@k (positive = F3 retrieved more positives); 1st = first positive rank.

| case_id | query (abbrev) | n_pos | F0@5 | F3@5 | d@5 | F0@10 | F3@10 | d@10 | F0@20 | F3@20 | d@20 | F0_1st | F3_1st |
|---------|---------------|-------|------|------|-----|-------|-------|------|-------|-------|------|--------|--------|
| v3.1h-001 | Metformin hepatic gluconeogenesis | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 |
| v3.1h-002 | Lisinopril clearance | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-021 | Warfarin + aspirin bleeding | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-022 | Fluconazole-warfarin CYP2C9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-023 | Lisinopril-spironolactone hyperkalemia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-046 | Idiosyncratic DILI mechanisms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-047 | Spironolactone hyperkalemia risk | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 |
| v3.1h-066 | Metformin renal contraindication | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-067 | Warfarin INR monitoring | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |
| v3.1h-069 | Drug-induced hepatotoxicity | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - |

---

## 3. Promotion / Demotion of Labelled Positives (F0 rank -> F3 rank)

| case_id | document_id | F0 rank | F3 rank | delta | direction |
|---------|-------------|---------|---------|-------|-----------|
| v3.1h-001 | 41177211 | 1 | 1 | 0 | UNCHANGED |
| v3.1h-047 | 42374912 | 1 | 1 | 0 | UNCHANGED |

Summary:
  Positive docs tracked: 2
  Promoted (rank improved F0->F3): 0
  Demoted  (rank worsened F0->F3): 0
  Unchanged:                        2

---

## 4. Diagnostic Findings and Interpretation

### 4.1 Very sparse positive label coverage
Only 2 of 98 labelled documents (2.0%) are adjudicated positive across the
10 pilot cases. Both positive documents ranked #1 in F0 already. This means
the annotated label set provides minimal signal to distinguish F0 from F3
reranking behaviour for this pilot.

### 4.2 Both positives already at rank 1 in F0
The two confirmed positive documents were retrieved at F0_rank=1 by BM25+dense+graph+RRF.
MedCPT reranking (F3) preserved their rank-1 position. This shows the hybrid
retrieval baseline (F0) successfully surfaced both labelled positives at the
top of the candidate pool.

### 4.3 No reranking effect observable on labelled positives
With only 2 positive documents, both at rank 1 in both F0 and F3, the delta
metrics are all zero. The diagnostic cannot characterise promotion or demotion
behaviour from this label set alone.

### 4.4 Unlabelled candidates
The F0 candidate pool contains 60 documents per case (600 total across 10 cases).
The annotation set covers 98 of those 600 candidate positions. The remaining
502 candidate positions are unlabelled, meaning the measured hit@k values are
a lower bound on potential true relevance.

### 4.5 What this means for Phase 2F.5B
The annotation coverage is too sparse to support a rigorous F0-vs-F3 comparison
on the labelled signal alone. Phase 2F.5B (independent confirmation) would need
either:
  (a) Expanded annotation coverage of the F0 candidate pool, or
  (b) An independent annotator reviewing a larger fraction of the 60-document
      pool per case.

---

## 5. Failure Pattern Analysis

### Cases with zero labelled positives (8 of 10)
v3.1h-002, v3.1h-021, v3.1h-022, v3.1h-023, v3.1h-046, v3.1h-066, v3.1h-067, v3.1h-069

These cases have no annotated supporting evidence in the 248-document corpus.
Two interpretations:
  (a) The corpus genuinely lacks strong supporting evidence for these queries
      (corpus coverage gap), or
  (b) Relevant documents exist in the corpus but were not included in the
      annotation candidate set (annotation coverage gap).

Distinguishing these requires either exhaustive corpus annotation or
an independent evidence search against a broader source.

### Cases with labelled positives (2 of 10)
v3.1h-001 (metformin hepatic gluconeogenesis): 1 positive at rank 1 in both F0 and F3.
v3.1h-047 (spironolactone hyperkalemia risk): 1 positive at rank 1 in both F0 and F3.

---

## 6. Artifact Provenance

All results derived from the canonical Phase 2F.5A-REAL-REPRODUCED run:

  f0_results.jsonl SHA256 = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
  f3_results.jsonl SHA256 = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
  debug_records.jsonl SHA256 = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362

Annotation sources (read-only, not used during retrieval):
  experiments/annotations/v3_1_human/pilot/reviewer_workspace/decision_helper_review.csv
  experiments/annotations/v3_1_human/pilot/false_negative_screen_v2/human_review_queue.csv

---

## 7. Conclusion

CLEAN_REPRODUCTION_VALID = YES (from canonical run integrity report)
DIAGNOSTIC_ANALYSIS_COMPLETE = YES

The Phase 2F.5A pilot diagnostic cannot distinguish F0 from F3 reranking behaviour
on the current annotation set due to sparse positive coverage (2 positives across
10 cases, both already at rank 1 in F0). This is an annotation coverage finding,
not a negative result about retrieval quality.

Phase 2F.5B (independent confirmation) requires expanded annotation coverage
before a meaningful F0 vs F3 comparison can be made.

Phase 2F.5B: LOCKED - requires user approval and annotation expansion plan.
Phase 2G:    LOCKED - requires Phase 2F.5B completion.
