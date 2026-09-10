# Phase 2F.5A-REAL-REPRODUCED: Canonical Run Integrity Report

**Report generated:** 2026-09-03T20:15 IST
**Canonical run task:** task-9881
**Verification method:** OS-level PowerShell Get-FileHash -Algorithm SHA256 + independent Python hashlib.sha256
**Status:** CANONICAL RUN — ALL GATES PASS

> Research disclaimer: This is a research platform, not an FDA-approved clinical decision system.
> All outputs are evidence-grounded research results, not clinical advice.

---

## Gate Summary

  CANONICAL_RUN          = YES
  RUNNER_PROVENANCE      = PASS
  OUTPUT_HASH_INTEGRITY  = PASS
  CORPUS_ID_VALIDITY     = PASS
  F0_F3_SET_EQUALITY     = PASS
  DUPLICATE_CHECK        = PASS
  MEDCPT_SCORE_ALIGNMENT = PASS
  ANNOTATION_LEAKAGE     = PASS
  QUERY_SET_HASH_VALIDITY= PASS

  CLEAN_REPRODUCTION_VALID = YES

---

## Execution Provenance

  Pre-execution runner hash (PowerShell, before run):
    774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5

  Post-execution runner hash (PowerShell, after run — must match):
    774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5

  Pre/post match: TRUE — runner was not modified during or after execution.

  manifest[runner_sha256] (self-recorded by runner at startup):
    774c9d65cae1b6e83a945d5c773d8fc07ff0043c806975428d8b4e5ddc13f9a5

  Manifest runner hash matches current runner: TRUE

  Execution timestamp (UTC, from manifest): 2026-09-03T14:43:31.102844Z
  Working directory: C:\Users\sunny\Downloads\CASE STUDY
  Command: uv run python runner_real_hardened.py

  Execution markers confirmed in stdout:
    REAL_RETRIEVAL_LOOP_STARTED
    PROCESSING_CASE=v3.1h-001  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-002  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-021  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-022  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-023  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-046  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-047  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-066  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-067  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    PROCESSING_CASE=v3.1h-069  F0_CANDIDATES=60  MEDCPT_SCORES=60  F3_CANDIDATES=60
    REAL_RETRIEVAL_LOOP_COMPLETED

---

## Actual SHA-256 Hashes (all OS-computed, independent of runner output)

  RUNNER_SHA256        = 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
  F0_SHA256            = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
  F3_SHA256            = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
  DEBUG_SHA256         = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
  MANIFEST_SHA256      = 8CD7CB9FAF3B34A09CF77B5C89534E062A2614BE8C4DDCDEBB3CBC00246F6741
  OUTPUT_HASHES_SHA256 = 063BA53F06E88A16AD11D7EC62FBC30FA44F5B9096B414445F8E313842FCF0DC
  CORPUS_SHA256        = E4346AD15EC1F74AF9ECC010EF822503EB44638F1020E7F0FCB51AD5C58F42F7
  QUERY_SET_SHA256     = B09B7FEC7A3DB1FB90DB665986444FF27C716D119E9788FC3CB1948E3FC53FC6

---

## Output Hash Cross-Verification

Hashes stored in output_hashes.json (written by runner) vs independently recomputed:

  debug_records.jsonl:
    stored = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
    actual = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
    MATCH  = TRUE

  f0_results.jsonl:
    stored = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
    actual = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
    MATCH  = TRUE

  f3_results.jsonl:
    stored = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
    actual = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
    MATCH  = TRUE

---

## Content Integrity

  Records in f0_results.jsonl:    10
  Records in f3_results.jsonl:    10
  Records in debug_records.jsonl: 10

  Case IDs present in all files:
    v3.1h-001, v3.1h-002, v3.1h-021, v3.1h-022, v3.1h-023,
    v3.1h-046, v3.1h-047, v3.1h-066, v3.1h-067, v3.1h-069

  F0/F3 set equality (all 10 cases):     PASS
  No duplicate IDs in F0 (all 10 cases): PASS
  No duplicate IDs in F3 (all 10 cases): PASS
  MedCPT input == F0 ranking (all 10):   PASS

---

## Corpus Validity

  Corpus file: experiments/evidence_snapshots/retrieval-v3-real/documents.json
  Corpus SHA256: E4346AD15EC1F74AF9ECC010EF822503EB44638F1020E7F0FCB51AD5C58F42F7
  Corpus document count: 248

  All F0 IDs exist in frozen corpus: PASS
  All F3 IDs exist in frozen corpus: PASS

---

## Annotation Leakage Check

  Checked runner source for: human_final_label, adjudicated, decision_helper_review
  Result: ABSENT — no annotation-loading code found in runner.

---

## Retrieval Methodology (unchanged)

  F0: BM25 + S-PubMedBERT (pritamdeka/S-PubMedBert-MS-MARCO) + Graph + RRF(k=60)
      top_k=60 candidates per case
  F3: F0 candidate pool re-ranked by ncbi/MedCPT-Cross-Encoder
      60 candidates scored and re-sorted by cross-encoder score

---

## Archive Record

  Execution 2 artifacts archived to:
  experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced-archive-execution2/
  (identical hashes — canonical run produced the same deterministic results)

---

## Final Decision

  CLEAN_REPRODUCTION_VALID = YES

  All integrity gates have passed. This is the canonical Phase 2F.5A-REAL-REPRODUCED run.

  Phase 2F.5B (Independent Confirmation): LOCKED — requires user approval to proceed.
  Phase 2G (Production Integration): LOCKED — requires Phase 2F.5B completion.
  Performance analysis: NOT PERFORMED — awaiting user approval.

