# Annotation Coverage Gap Baseline
## Phase 2F.5B-Prep Pre-Annotation Baseline

**Generated:** 2026-09-03 IST
**Canonical run:** task-9881 | F0 SHA256: 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A

This document records the annotation coverage baseline before Phase 2F.5B-Prep
expansion annotation begins. It must NOT be modified after annotation starts.

---

## Coverage Summary

| Metric | Value |
|--------|-------|
| F0 candidate positions (10 cases x 60) | 600 |
| Positions with existing labels | 70 |
| **Unlabelled positions requiring expansion** | **530** |
| Confirmed positive labels | 2 |
| Cases with zero positives | 8 of 10 |

---

## Per-Case Breakdown

| case_id | F0 pool | Labelled | Unlabelled | Positives | Existing label distribution |
|---------|---------|----------|------------|-----------|-----------------------------|
| v3.1h-001 | 60 | 10 | 50 | 1 (rank 1) | DIRECT_SUPPORT:1, NOT_RELEVANT:9 |
| v3.1h-002 | 60 | 8 | 52 | 0 | NO_EVIDENCE:2, NOT_RELEVANT:6 |
| v3.1h-021 | 60 | 9 | 51 | 0 | NOT_RELEVANT:7, NO_EVIDENCE:2 |
| v3.1h-022 | 60 | 7 | 53 | 0 | NOT_RELEVANT:6, NO_EVIDENCE:1 |
| v3.1h-023 | 60 | 7 | 53 | 0 | NO_EVIDENCE:1, NOT_RELEVANT:6 |
| v3.1h-046 | 60 | 9 | 51 | 0 | NOT_RELEVANT:8, NO_EVIDENCE:1 |
| v3.1h-047 | 60 | 7 | 53 | 1 (rank 1) | DIRECT_SUPPORT:1, NOT_RELEVANT:6 |
| v3.1h-066 | 60 | 6 | 54 | 0 | NO_EVIDENCE:1, NOT_RELEVANT:5 |
| v3.1h-067 | 60 | 4 | 56 | 0 | NOT_RELEVANT:4 |
| v3.1h-069 | 60 | 3 | 57 | 0 | NOT_RELEVANT:2, NO_EVIDENCE:1 |

---

## Known Positives (pre-expansion)

| case_id | document_id | F0 rank | F3 rank | label |
|---------|-------------|---------|---------|-------|
| v3.1h-001 | 41177211 | 1 | 1 | DIRECT_SUPPORT |
| v3.1h-047 | 42374912 | 1 | 1 | DIRECT_SUPPORT |

Both positives were ranked #1 by F0 (BM25+dense+graph+RRF) and remained at #1
after MedCPT reranking (F3).

---

## Expansion Workspace

Annotation queues created at:
  experiments/annotations/v3_1_human/pilot/expansion_v1/
    reviewer_A_expansion.csv   (530 rows, rank-blinded)
    reviewer_B_expansion.csv   (530 rows, rank-blinded)
    expansion_metadata.csv     (530 rows, backend: f0_rank, f3_rank, medcpt_score)
    expansion_manifest.json

Reviewer queues SHA256: ba2f138874b93a88... (identical for A and B)

---

## Freeze Confirmation

This baseline was computed from the frozen canonical run output and must not change:

  - runner_real_hardened.py was NOT re-executed to produce this baseline.
  - f0_results.jsonl and debug_records.jsonl are frozen (SHA256 verified).
  - The corpus (248 documents) is frozen.
  - Annotation expansion does NOT change F0 or F3 rankings.
