# Phase 2F.5A-REAL-REPRODUCED: Forensic Provenance Audit

**Report generated:** 2026-09-03T19:37 IST
**Verification method:** OS-level PowerShell Get-FileHash -Algorithm SHA256 and independent Python hashlib.sha256 re-computation.
**Status:** INDEPENDENT FORENSIC VERIFICATION

> Disclaimer: This is a research platform. All outputs are evidence-grounded research results, not clinical advice.

---

## Section 1: Actual SHA-256 Hashes (OS-computed, not runner-reported)

All hashes computed independently via PowerShell Get-FileHash -Algorithm SHA256 and verified
against a second independent Python hashlib.sha256 calculation. These replace all prior
placeholder/fabricated hash values.

| File | ACTUAL SHA-256 |
|------|----------------|
| runner_real_hardened.py | 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5 |
| f0_results.jsonl | 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A |
| f3_results.jsonl | 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36 |
| debug_records.jsonl | 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362 |
| execution_manifest.json | F029F08D1829A4952EB08D13010FEC01B3112246CE790353B79AB9717345038F |
| output_hashes.json | 063BA53F06E88A16AD11D7EC62FBC30FA44F5B9096B414445F8E313842FCF0DC |

Named fields:

  ACTUAL_RUNNER_SHA256        = 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
  ACTUAL_F0_SHA256            = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
  ACTUAL_F3_SHA256            = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
  ACTUAL_DEBUG_SHA256         = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
  ACTUAL_MANIFEST_SHA256      = F029F08D1829A4952EB08D13010FEC01B3112246CE790353B79AB9717345038F
  ACTUAL_OUTPUT_HASHES_SHA256 = 063BA53F06E88A16AD11D7EC62FBC30FA44F5B9096B414445F8E313842FCF0DC

---

## Section 2: Execution Timeline (IST = UTC+5:30)

| Event | Timestamp (IST) |
|-------|-----------------|
| Runner first created on disk | 2026-09-03 15:42:30 |
| Execution 1 launched (task-9799) | 2026-09-03 16:08:52 |
| Runner edited (added result-file writes + manifest) | 2026-09-03 16:10:46 |
| Execution 2 launched (task-9817) | 2026-09-03 16:10:54 |
| f0_results.jsonl created on disk | 2026-09-03 19:05:13 |
| f3_results.jsonl created on disk | 2026-09-03 19:05:13 |
| execution_manifest.json written | 2026-09-03 19:06:01 |
| output_hashes.json written | 2026-09-03 19:06:01 |

KEY FINDING: Execution 1 started BEFORE the edit at 16:10:46 and did not write
f0/f3/manifest/output_hashes. All final result files were produced exclusively
by Execution 2 (task-9817).

---

## Section 3: Execution Provenance

  EXECUTION_1_RUNNER_HASH = UNKNOWN
    Reason: Runner was edited after Execution 1 and before Execution 2.
    No git history available to recover the pre-edit source hash.
    Execution 1 produced only debug_records.jsonl (creation time 15:44:42 IST,
    before the edit). That file was overwritten by Execution 2.

  EXECUTION_2_RUNNER_HASH = 774c9d65cae1b6e83a945d5c773d8fc07ff0043c806975428d8b4e5ddc13f9a5
    Source: Runner hashed itself at startup via Path(__file__) / hashlib.sha256
    and recorded the result in execution_manifest.json["runner_sha256"].
    Independent OS verification:
      manifest[runner_sha256]  = 774c9d65cae1b6e83a945d5c773d8fc07ff0043c806975428d8b4e5ddc13f9a5
      OS hash of current runner = 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
      Match = TRUE

  FINAL_ARTIFACT_PRODUCER = Execution 2 (task-9817, 2026-09-03 16:10:54 IST)

---

## Section 4: Output Hash Cross-Verification

| File | Stored in output_hashes.json | OS-independent re-hash | Match |
|------|------------------------------|------------------------|-------|
| debug_records.jsonl | 6cbd595a...2366d362 | 6CBD595A...2366D362 | PASS |
| f0_results.jsonl | 15b19e54...4c0846a | 15B19E54...4C0846A | PASS |
| f3_results.jsonl | 45e54b61...819f36 | 45E54B61...819F36 | PASS |

All stored hashes match independent recomputation. Files not modified since Execution 2.

---

## Section 5: Content Integrity

| Check | Result |
|-------|--------|
| f0_results.jsonl records | 10 |
| f3_results.jsonl records | 10 |
| debug_records.jsonl records | 10 |
| set(F0) == set(F3) all 10 cases | PASS |
| No duplicate IDs in F0 all 10 cases | PASS |
| No duplicate IDs in F3 all 10 cases | PASS |
| medcpt_input_ids == f0_ranked_ids all 10 cases | PASS |
| Annotation leakage | PASS - no annotation-loading code in runner |

---

## Section 6: Summary

  ACTUAL_RUNNER_SHA256        = 774C9D65CAE1B6E83A945D5C773D8FC07FF0043C806975428D8B4E5DDC13F9A5
  ACTUAL_F0_SHA256            = 15B19E54B03DDBD2BC513CAC3800A73303DAC11408DB8D6484B62829B4C0846A
  ACTUAL_F3_SHA256            = 45E54B6143531747F6FDE9778BC0391F26CC90D09AC041708005EF6DD6819F36
  ACTUAL_DEBUG_SHA256         = 6CBD595A4AFB1F153CDC5FFF8D2EDCF03241E4AD1319018AFDC73DDF2366D362
  ACTUAL_MANIFEST_SHA256      = F029F08D1829A4952EB08D13010FEC01B3112246CE790353B79AB9717345038F
  ACTUAL_OUTPUT_HASHES_SHA256 = 063BA53F06E88A16AD11D7EC62FBC30FA44F5B9096B414445F8E313842FCF0DC

  EXECUTION_1_RUNNER_HASH  = UNKNOWN (runner edited before Execution 2; Execution 1 produced no final result files)
  EXECUTION_2_RUNNER_HASH  = 774c9d65cae1b6e83a945d5c773d8fc07ff0043c806975428d8b4e5ddc13f9a5
  FINAL_ARTIFACT_PRODUCER  = Execution 2 (task-9817)

  PROVENANCE_STATUS = PARTIAL
    All result files produced exclusively by Execution 2 with a confirmed runner hash.
    Execution 1 runner source hash is unrecoverable (no git history).

  CLEAN_REPRODUCTION_VALID = PENDING USER DECISION
    (See Section 7 open question)

---

## Section 7: Open Provenance Question for User Review

EVIDENCE FOR VALIDITY:
- All result files were produced exclusively by Execution 2.
- The runner hashed itself at startup before writing any results.
  The hash in the manifest matches the current runner exactly.
- The retrieval methodology was NOT changed between executions.
  Only result-file writing and manifest generation code was added in the edit.
- All content invariants (F0/F3 set equality, no duplicates, MedCPT alignment) pass.

EVIDENCE AGAINST VALIDITY:
- Execution 1 ran with a runner that did not write result files.
  That debug file was overwritten by Execution 2.
- Runner source hash for Execution 1 is UNKNOWN (no git history).
- Cannot cryptographically prove Execution 1 and Execution 2 used identical retrieval logic.

RECOMMENDATION:
If the unknown Execution 1 runner hash is unacceptable, run the clean reproduction
once more from the current runner (774C9D65...) with no further edits. This would
produce a fully auditable single-execution record with no provenance ambiguity.

---

No performance analysis performed. Phase 2F.5B and Phase 2G remain LOCKED.
