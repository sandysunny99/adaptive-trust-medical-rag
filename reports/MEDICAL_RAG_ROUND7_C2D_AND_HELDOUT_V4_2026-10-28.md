# Medical RAG round 7, candidate C2d: attribution-object role, drug-role anaphor antecedents, plus the held-out V4 measurement (2026-10-28)

Research prototype. **Preliminary engineering evidence; no clinical validation.** Labels are AI-preliminary. C3 has not started.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Engineering validation of C2d | **Pass.** Backend normal and blocked: 2038 passed, 4 skipped each. vitest 148/148. tsc, oxlint, ruff, bandit, whitespace, the scoped gitleaks scan and the integrity checks all pass. |
| V3 failures (V3-NEG-01, V3-CMP-05, V3-ADJ-09, V3-ANA-03) | **All fixed.** The three attribution claims are rejected by the gate itself; V3-ANA-03 passes. |
| Held-out V4: unsupported releases | **0 of 28 released.** 3 of 28 missed by the gate and stopped only by the real NLI. |
| Held-out V4: identity false withholds | 1 / 44 (2.3%) |
| Medication-identity coverage | **BLOCKED (recommended).** No unsupported claim was released, but 3 known wordings pass the gate, so release depends on the NLI. The same rule was applied to V2's H-NEG-13. |
| Evidence support | Unchanged |
| Nutrition-source suitability | See `MEDICAL_RAG_NUTRITION_SOURCE_AUDIT_PASS2_AND_PERMISSIONS_2026-10-28.md` |
| Clinical validation | None |

## 1. Candidate

- **C2c verified first:** 55 files OK, HEAD `2190fb0`. C1 mappings 6851 / 221124 / 203191 / 203191. V3 artifacts OK.
- **C2d copy:** `C:\Users\sunny\r7-c2d-gate`, a clone at `2190fb0` (detached, `origin` removed) plus the 55 C2c files plus the V3 results. Verified 55 OK before any edit.
- **Frozen:** 23:03:26 +05:30, 66 files (`c2d_fingerprint.txt`, `2b45186b…`). All OK after every run.
- **The owner's C2c manual-test servers** (5180 and 8020) were not touched and are still running.

## 2. Held-out V4, frozen before any code change

`experiments/round7_medication_role_v4/` was frozen at 22:53:17. The manifest records C2c's gate hash `9326c1cd…` and 0 code changes. A hashed copy is in `C:\Users\sunny\r7-c2d-work\heldout_v4_frozen\` and was verified unchanged after the run.

| Item | Hash / count |
|---|---|
| `CRITERIA_V4.md` (V3 + I attribution object, J drug-role antecedents, K held-out rule) | `9932c8ee…5e` |
| `MEDROLE_HELDOUT_V4.jsonl` | `fcff7b12…24`, **72 rows, all constructed** |
| `review/BLIND_REVIEW_PACKET_V4.csv` | `2c117982…d0` |

- **Two labels were corrected before freezing:** V4-ANA-03's rationale, and one row reclassified as V4-ANA-09 (a "concomitant use" anaphor with no antecedent → REJECT under criteria J).
- **A wording decision not to follow V4:** while coding, I considered also matching "links Y to X" (the active form). I dropped it so the code would not be fitted to a held-out row. V4-DOC-03 then measured exactly that gap.

## 3. Changes (C2d relative to C2c)

| Change | Detail |
|---|---|
| **Attribution object** (`Role.ATTRIBUTION_OBJECT`) | "linked / attributed / attributable / ascribed / related / due / secondary **to X**". X is checked like an agent. A multi-word object with no medication in it ("due to CYP3A4 inhibition", "related to renal insufficiency") is treated as a described mechanism or condition, not a name. A lone name ("linked to Orbazine") is checked. The phrase cut now also stops at "leading / causing / resulting / increasing / raising / reducing / making". |
| **Anaphor antecedents** | Only medications in a **drug role** earlier in the answer count. An incidental lexicon term ("potassium") or a drug merely mentioned ("Furosemide is a loop diuretic.") is not an antecedent. |
| **"The medication"** | Bare "medication", "drug" and "agent" are singular anaphors. Role phrases arrive with the article stripped, and that was the real cause of V3-ANA-03 (not the antecedent count). Plurals ("Drugs that inhibit …") stay ordinary nouns. |

New: `tests/e2e/test_medication_role_gate_c2d.py` (15 tests), plus the V4 scripts `run_heldout_v4.py` and `heldout_metrics_v4.py`.

Diffs:
- gate: `C:\Users\sunny\r7-c2d-logs\C2d_vs_C2c_gate.diff` (84 lines, `7a56abfb…`)
- tests: `C2d_vs_C2c_tests.diff` (37 lines)

**Changed expectations (4 tests in C2b/C2/unit files):** anaphor positive controls used the antecedent sentence "Lisinopril and spironolactone are named in section 7.1". That sentence puts no drug in a role, so under criteria J it no longer provides antecedents. The sentence became "Lisinopril interacts with spironolactone [Source N]." The unit "singular with two referents" case now gets its two referents from that drug-role sentence.

## 4. Validation (frozen C2d; logs in `C:\Users\sunny\r7-c2d-logs\`)

| Check | Result |
|---|---|
| Focused: C2d (15), C2c (16), C2b (23), gate unit and e2e, live semantics, alignment, guard, normaliser (C1's 5) | all pass (259 before freeze) |
| Backend, normal network | **2038 passed, 4 skipped**, exit 0 (23:03:43–23:10:18) |
| Backend, network blocked | **2038 passed, 4 skipped**, exit 0 (23:10:18–23:20:09) |
| Count | C2c 2027 + 15 = 2042 = 2038 + 4 |
| vitest (`--maxWorkers=1`) / `tsc -b` / oxlint | 148/148 / exit 0 / exit 0, with the same 3 warnings |
| ruff / bandit / whitespace | pass / exit 0 / clean |
| gitleaks `dir --redact` | no leaks; scope: copies of the **66 frozen files only** |
| Integrity scripts / frozen data | PASS, PASS, 311 pinned; eval set `bd23fe48…`, lexicon `bcf0d184…`, cache `a80146bd…`; protected paths: no diff |
| **Frozen 42-set**, real NLI | 9 released, 0 false releases, the same 5 false withholds, gate rejections only on D05, E08 and E27, **no outcome change** |

The 4 skips are the provider-credential tests (no `.env.local` in the copy).

## 5. Held-out V4 (real NLI, scripted generation, 72 rows on the full path)

`results/HELDOUT_RESULTS_V4.jsonl` (`52de41ff…`), `results/HELDOUT_METRICS_V4.json` (`c6f45312…`).

**A. Identity false withholds: 1 / 44 (2.3%).** Every category is 0 except attribution, at 1 / 10:
- **V4-ATT-20:** "Bleeding secondary to argatroban may increase with warfarin." The effect-subject pattern took "Bleeding secondary" as the subject.

**B. Unsupported claims: 28 tested, 25 rejected by the gate, 3 missed, 0 released**

| Pattern | Tested | Rejected | Missed |
|---|---|---|---|
| linked to | 4 | 4 | 0 |
| attributed to | 2 | 2 | 0 |
| related to | 2 | 2 | 0 |
| due to | 1 | 1 | 0 |
| secondary to | 2 | 2 | 0 |
| compound (linked / attributed / related) | 3 | 3 | 0 |
| missing / ungrounded antecedent | 4 | 4 | 0 |
| **passive** | 2 | 1 | **1 (V4-PAS-02)** |
| **ambiguous antecedent** | 1 | 0 | **1 (V4-ANA-05)** |
| **document hides entity** | 1 | 0 | **1 (V4-DOC-03)** |
| other (combination, structured, instruction, effect first, effect subject, class member) | 6 | 6 | 0 |

The three misses, each withheld only because the real NLI did not entail it:
- **V4-PAS-02:** "Bleeding may be intensified by Quospar …". "Intensified by" is not in the passive-verb list.
- **V4-ANA-05:** "Diclofenac raises bleeding risk with warfarin. It requires dose review." The predicate "requires dose review" is not a drug-effect pattern, so "It" got no role at all.
- **V4-DOC-03:** "The FDA label for warfarin links bleeding to Pyranex." The active "links Y to X" is not matched; this was deliberately not added (§2).

**D. Compound claims:** 5 / 5 correct, with the failing clause surfaced.

**E. Final behaviour (72 rows):**

| Identity gate | Released | Withheld |
|---|---|---|
| PASS | 30 | 16 |
| REJECT | 0 | 26 |

## 6. Residual blockers and assessment

- **Pattern-by-pattern closure has diminishing returns.** Each round closes its failures and the next held-out set finds 1–3 new wordings. V2 had 1 miss; V3 had 1 release and 2 misses; V4 had 0 releases and 3 misses. The bounded-pattern approach can't promise coverage of open-ended English.
- **Options for the owner:**
  - (a) another small round (passive "intensified by", "links Y to X", instruction predicates such as "requires dose review", and the "Y secondary to X may …" subject boundary);
  - (b) a structural change: treat **any** unresolved, medication-like name anywhere in a statement about drug effects as needing grounding. That is broader, and its false-withhold cost must be measured;
  - (c) accept "0 released on V4" with the NLI as a second line, and record the residual risk.

  The owner's earlier rule makes (c) a policy decision, so I recommend keeping coverage BLOCKED until the owner chooses.

## 7. Final state

- **C2d:** 66 files frozen and OK, plus the V4 results.
- **Untouched:** C2c (55 OK; its servers still running), C2b (44), C2 (35), C1 (27), M1 (15), and the Round-6 checkout (24 OK, the same 9 tracked changes).
- **Nothing staged, committed or pushed.**
