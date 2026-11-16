# Medical RAG round 7, candidate C2c: H-NEG-13 and H-ORD-09, plus the held-out V3 measurement (2026-10-28)

Research prototype. **Preliminary engineering evidence; no clinical validation.** Labels are AI-preliminary. C3 has not started.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Engineering validation of C2c | **Pass.** Backend normal and blocked: 2023 passed, 4 skipped. vitest 148/148 (rerun with one worker; see §4). tsc, oxlint, ruff, bandit, whitespace and the scoped gitleaks scan are clean, and the integrity checks pass. |
| H-NEG-13 and its equivalents | **Fixed.** Rejected by the identity gate itself (5 combiner forms). |
| H-ORD-09 | **Fixed.** Passes the gate, with no exact-string exception. |
| Held-out V3: unsupported releases | **1 of 36 RELEASED as verified (V3-NEG-01).** 3 of 36 missed by the gate. |
| Held-out V3: identity false withholds | 1 / 65 (1.5%), V3-ANA-03 |
| Medication-identity coverage | **BLOCKED.** A new wording family ("linked to / attributed to X") still releases an unsupported claim. |
| Evidence support | Unchanged |
| Clinical validation | None |

## 1. Starting state and candidate

- **C2b:** 44-file fingerprint OK, HEAD `2190fb0`. V2 artifacts OK, and the V2 results are hashed.
- **C2c copy:** `C:\Users\sunny\r7-c2c-gate`, a clone at `2190fb0` (detached, `origin` removed) plus the 44 C2b files (verified) plus the V2 results.
- **Frozen:** 2026-10-28 21:52:21 +05:30, 55 files (`c2c_fingerprint.txt`, `d480f4cf…`). All OK after every run.

## 2. Held-out V3, frozen before any code change

`experiments/round7_medication_role_v3/` was frozen at 21:42:08. The manifest records the gate and `live_application.py` hashes of C2b at freeze time, with 0 code changes. A hashed copy is in `C:\Users\sunny\r7-c2c-work\heldout_v3_frozen_final\` and was verified unchanged after the run.

| Item | Hash / count |
|---|---|
| `CRITERIA_V3.md` (V2 + F participle adjectives, G combination participants, H held-out rule) | `753fb03d…f5e` |
| `MEDROLE_HELDOUT_V3.jsonl` | `8bb15ee6…102`, **101 rows, all constructed** |
| `review/BLIND_REVIEW_PACKET_V3.csv` | `813ab9ab…c2c` |

Categories: ordinary 15, combination 12, adjective-vs-verb 10, negative 20, compound 6, anaphor 4, drug class 6, contextual 6, document subject 6, common word 5, proper noun 5, non-medical 6. V3 uses new medications (prasugrel, diclofenac, escitalopram, duloxetine, piroxicam, sulindac and others) and new invented names (Tenvolix, Orbazine, Klemadrine, Nuvraxa, Dorvastatin).

## 3. Change (C2c relative to C2b)

There is one source change, in `verification/medication_role_gate.py`; the diff is `C:\Users\sunny\r7-c2c-logs\C2c_vs_C2b_gate.diff`, 33 lines, `0a846661…`.

- **H-NEG-13:** `role_spans` now normalises combiners ("in combination with", "together with", "combined with", "alongside", "along with", "plus") **before** any phrase is cut. Each participant is then classified on its own; a grounded lisinopril never grounds the other drug.
- **H-ORD-09:** an effect-verb match whose subject phrase ends in a determiner (`a`, `an`, `the`, `this`, …) is a participle adjective ("A reduced starting dose"), so it is not read as a subject. "That" is excluded, because it is also the relativizer in "drugs that increase", which the C2b subject boundary handles.

Also new:
- `tests/e2e/test_medication_role_gate_c2c.py` (16 tests): 5 combination forms, rejection that cannot be undone downstream, 3 grounded combinations, 3 participle adjectives, and 4 genuine verbs, passives or effect-first claims still read.
- V3 scripts: `run_heldout_v3.py` and `heldout_metrics_v3.py`, copies of the V2 scripts with new paths.

Frontend, data, cache (C1), lexicon, prompts, NLI model, trust settings and relationship records: no change.

## 4. Validation (frozen C2c; logs in `C:\Users\sunny\r7-c2c-logs\`)

| Check | Result |
|---|---|
| Focused: C2c (16), C2b (23), gate e2e and unit, live failure semantics, citation alignment, guard, normaliser (C1's 5) | 244 passed |
| Backend, normal network | **2023 passed, 4 skipped**, exit 0 (21:52:34–21:59:24) |
| Backend, network blocked | **2023 passed, 4 skipped**, exit 0 (21:59:24–22:07:11) |
| Count | C2b 2011 collected + 16 new = **2027** = 2023 passed + 4 skipped |
| vitest | **148/148** with `--maxWorkers=1`. The first, parallel run started while the local servers and NLI were running: 13 workers failed to start ("Timeout waiting for worker to respond"), 9 files and 24 tests passed, and no test assertion failed. |
| tsc / oxlint | exit 0 / exit 0, with the same 3 warnings in untouched files |
| ruff / bandit / whitespace | pass / exit 0 / clean |
| gitleaks `dir --redact` | no leaks; scope: copies of the **55 frozen files only** |
| Integrity scripts | PASS, PASS, 311 pinned |
| Frozen data | eval set `bd23fe48…`, lexicon `bcf0d184…`, cache `a80146bd…` (C1); protected paths: no diff |
| **Frozen 42-set**, real NLI | 9 released, 0 false releases, the same 5 false withholds, gate rejections only on D05, E08 and E27, **no outcome change** |

The 4 skips are the provider-credential tests (no `.env.local` in the copy, deliberately).

## 5. Held-out V3 (real NLI, scripted generation, all 101 rows on the full path)

`results/HELDOUT_RESULTS_V3.jsonl` (`2e80bcb6…`), `results/HELDOUT_METRICS_V3.json` (`83603448…`).

**A. Identity false withholds: 1 / 65 (1.5%).** Every category is 0 except anaphor, at 1 / 3. **V3-ANA-03** is "Lisinopril is associated with hyperkalemia [Source 1]. The medication can raise serum potassium [Source 1]." The singular anaphor was rejected, most likely because the earlier sentence's lexicon mentions included more than one medication-like term. Combination 0 / 6; adjective-vs-verb 0 / 7; document subject 0 / 5.

**B. Unsupported claims: 36 tested, 33 rejected by the gate, 3 missed, 1 released**

| Missed row | Wording | Final |
|---|---|---|
| **V3-NEG-01** | "Hyperkalemia is frequently **linked to** Orbazine [Source 1]." | **RELEASED as verified.** The pattern read "Hyperkalemia" as the subject, and "linked to X" never put X in a role. |
| V3-CMP-05 | "…, because hyperkalemia is **linked to** Nuvraxa [Source 1]." | Withheld only by the NLI (non-entailment) |
| V3-ADJ-09 | "An increased risk of hyperkalemia is **attributed to** Klemadrine [Source 1]." | Withheld only by the NLI |

These were caught: all 7 combination negatives, including "receiving lisinopril together with metamizole"; all passives (4); implicit subjects (3); nested (2); uncited instructions (2); structured fields; wrong brand; the ambiguous name; and the document phrase hiding an invented drug.

**D. Compound claims:** 5 of 6 correct. V3-CMP-05 is the "linked to" miss above.

**E. Final behaviour (101 rows):**

| Identity gate | Released | Withheld |
|---|---|---|
| PASS | 41 | 26 |
| REJECT | 0 | 34 |

## 6. Residual blockers

1. **"Y is linked to X", "Y is attributed to X"** (V3-NEG-01, released; V3-CMP-05; V3-ADJ-09): the effect is the grammatical subject and the drug is the object of "to". This needs an object role for "linked/attributed/related/due/secondary to X", with the subject treated as the effect. That is a new candidate, measured on yet another held-out set.
2. **A singular anaphor after a sentence whose lexicon mentions include a non-drug term** (V3-ANA-03): a false withhold. The antecedent list should count only drug-role entities, not every lexicon mention.

Medication-identity coverage stays **BLOCKED** (item 1).

## 7. Local manual test (owner-authorised env access, 2026-10-28)

- **Servers:** the C2c backend on 127.0.0.1:8020 and the frontend on 127.0.0.1:5180. Both are started by launchers outside the repository (`C:\Users\sunny\r7-c2c-work\local-test\`).
- **Credentials:** the backend loads the original checkout's `.env.local` and `.env` into its own process. Required names were checked set/missing only (GROQ_API_KEY set). The C2c copy contains only `.env.example`. None of the 11 secret values appears in the server logs or saved responses; this was checked without printing them.
- **Shipped evidence only:** the request abstained before generation, because no evidence record is approved.
- **With test-only approved copies** of FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 in a temp folder (as in the round 5/6 browser checks; nothing approved in the repository), one real Groq request for lisinopril + spironolactone:
  - served by `openai/gpt-oss-120b`, trust 0.663 (R2, threshold 0.60);
  - every stage ran; 5 of 6 claims verified with gate PASS;
  - the 6th was rejected by the identity gate ("spironolactone" not named by its cited source), so the answer abstained.
- **Not done:** no browser UI check was automated (the Playwright MCP is unavailable); the owner is testing manually.

## 8. Final state

- **C2c:** 55 files frozen and OK, plus V3 results.
- **Untouched:** C2b (44 OK), C2 (35 OK), C1 (27 OK), M1 (15 OK), and the Round-6 checkout (24 OK, the same 9 tracked changes).
- **Nothing staged, committed or pushed.**
- **Servers:** still running for the owner's manual test.
