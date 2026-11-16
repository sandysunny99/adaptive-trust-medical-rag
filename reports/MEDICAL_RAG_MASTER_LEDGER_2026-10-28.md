# Medical RAG master ledger (2026-10-28, after C2b)

The single status ledger for the owner's freeze plan. It is rebuilt from what is on disk today, not from earlier reports. Research prototype: no clinical validation anywhere.

## Verified state of every candidate

| Candidate | Path | Base | Fingerprint (checked today) | Report |
|---|---|---|---|---|
| Round-6 checkout (original) | `C:\Users\sunny\Downloads\CASE STUDY` | branch `wip/pre-threads-20261022-1440`, HEAD `2190fb0` | 24/24 OK (`r6c_fingerprint.txt`); the same 9 tracked changes as on 27 Oct; only new reports added | `MEDICAL_RAG_ROUND6_MEDICATION_LEXICON_REPORT_2026-10-27.md` |
| Round-6 evidence | `C:\Users\sunny\round6-evidence-2026-10-27` | — | `SHA256SUMS.txt` OK | — |
| C1 cache corrections | `C:\Users\sunny\r7-c1-cache` | 2190fb0 + R6 + `b3a3d3e` patch | 27/27 OK | `MEDICAL_RAG_ROUND7_C1_CACHE_CORRECTIONS_2026-10-27.md` |
| C2 medication-role gate | `C:\Users\sunny\r7-c2-gate` | C1 + gate | 35/35 OK | `MEDICAL_RAG_ROUND7_C2_MEDICATION_ROLE_GATE_2026-10-27.md` |
| M1 measurement | `C:\Users\sunny\r7-m1-measure` | C2 (unmodified) | 35/35 OK; 15 M1 artifacts OK | `MEDICAL_RAG_ROUND7_M1_MEASUREMENT_2026-10-28.md` |
| **C2b** + held-out measurement | `C:\Users\sunny\r7-c2b-gate` | C2 + C2b | 44 files OK (`199fa234…`) | `MEDICAL_RAG_ROUND7_C2B_REMEDIATION_AND_HELDOUT_2026-10-28.md` |
| FOOD-CANDIDATE-1 | `C:\Users\sunny\food-candidate-1` | 2190fb0 + R6 (**not** C1 or C2) | diff `5eb3bb36…`, 15 files; not re-run by me today | `MEDICAL_RAG_FOOD_CANDIDATE_1_REPORT_2026-10-28.md` |
| Cache-fix branch | `.claude/worktrees/zealous-curran-3c90b2` | `b3a3d3e` on `main` | clean | (in C1 report) |
| Security branches | `.claude/worktrees/gallant-bouman-a850e6` (`fix/agent-guardrail-gaps`, `09ab153`), `nostalgic-faraday-bff5f0` (`d64f68c`), `clever-clarke-ce9634` (`claude/repair-skill-md-nul-bytes`, `d14656b`) | committed locally on 26 Oct, not pushed | not re-verified today | `CLAUDE_FEATURE_FINALIZATION_REPORT_2026-10-26.md`, `CLAUDE_FINAL_FOLLOWUP_REPORT_2026-10-26.md` |

## Workstreams

| Workstream | Verified status | Blockers | Next action | Depends on | Approvals | Done when |
|---|---|---|---|---|---|---|
| **A. C2b medication identity** | Done. The 10 M1 failures are rejected; held-out set: 0/40 released, **1/40 gate miss** (H-NEG-13, stopped only by the NLI), 1/79 false withhold (H-ORD-09) | H-NEG-13 "in combination with X" after an exposure verb; H-ORD-09 participle adjective | **C2c**: fix those two, then measure on **new** held-out rows (V3) | — | owner go for C2c | No known unsupported wording passes the gate; new held-out set measured |
| **B. Measurement** | M1 (AI labels) and held-out V2 (AI labels) done; owner's AI-proposed M1 labels saved separately (189/191 agree with mine, both AI) | No owner-reviewed labels; no real-model rows (no credentials in the copies) | Owner reviews `BLIND_REVIEW_PACKET_V2.csv` (and V1) when possible | A | owner review | Reviewed labels recorded beside the AI labels |
| **C. C3 relationship-effect scope** | Not started. Design in `MEDICAL_RAG_ROUND7_DESIGN_AND_TEST_PLAN_2026-10-27.md` §5 | — | Build on C2b/C2c; all records stay PENDING; effect proposals marked PROPOSED | A (C2c) | none to build; record approvals stay with the owner | E28 and the §5.5 regressions pass; full matrix |
| **D. Patient-aware food** | FOOD-CANDIDATE-1 done by the food thread: modes A–D, LLM-free stage, `NO_APPROVED_EVIDENCE` live; backend 1961 passed with 5 failures that also fail in its baseline (missing `.env.local`); vitest 159/159; browser not run | Built on R6 without C1/C2/C2b: it touches `live_application.py`, which C2/C2b also change, so integration must merge both | Re-verify its fingerprint, then port its diff onto the C2b/C3 base in the integration candidate | A, C | F2 nutrition source approval (only for real recommendations) | Ported, full matrix passes; Mode B stays `NO_APPROVED_EVIDENCE` |
| **E. Security / provider** | 26 Oct: three security branches committed locally and clean; open items are REL-LIVE-0004 approval, CI not run remotely, Linux gitleaks 8.21.2 unverified, `test_cli.py` writing tracked outputs | The owner's audit categories (timeouts, malformed provider responses, untrusted-text rendering and others) have **not** been re-checked against today's code | Audit against the C2b base, list confirmed issues with evidence, fix in-scope ones in a dedicated candidate | — (parallel to C) | none for the audit | Confirmed issues fixed and regression-tested; unrunnable provider checks disclosed |
| **F. Integration freeze** | Not started | A–E | One isolated integration candidate: C1 + C2b/C2c + C3 + food + security fixes, then the full matrix and the 7-verdict report | A–E | owner go; commit only with separate authorization | Freeze-readiness report |

## Current verdicts (not a freeze verdict)

| # | Area | Status |
|---|---|---|
| 1 | Engineering | Each candidate passes its own matrix; nothing is integrated |
| 2 | Medication identity | **BLOCKED** (H-NEG-13) |
| 3 | Evidence support and relationship scope | C3 not started |
| 4 | Patient-food workflow | Implemented in its own candidate, not integrated, browser not run |
| 5 | Security and provider | 26 Oct fixes on branches; the re-audit is pending |
| 6 | Research readiness | Not ready: no owner-reviewed labels, no real-model rows |
| 7 | Clinical validation | Absent |
