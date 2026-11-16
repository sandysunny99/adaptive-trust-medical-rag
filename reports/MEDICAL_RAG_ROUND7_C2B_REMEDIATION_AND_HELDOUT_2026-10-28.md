# Medical RAG round 7, candidate C2b: residual medication-identity bypasses, and a held-out measurement (2026-10-28)

Research prototype. **Preliminary engineering evidence; no clinical validation.** Labels are AI-preliminary and no owner review has been done yet. C3, food and security work have not started in this candidate.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Engineering validation of C2b | **Pass.** Every check run on the frozen C2b state passed (section 5). No browser run. |
| The 6 M1 releases and 4 NLI-only gate misses | **All 10 now rejected by the identity gate** through the live path (scripted generation; scripted and real NLI). |
| Held-out residual unsupported releases | **0 of 40** released. **1 of 40** missed by the gate and stopped only by the real NLI (H-NEG-13, section 6). |
| Held-out identity false withholds | **1 of 79** (1.3%), H-ORD-09 (section 6). |
| Medication-identity coverage | **BLOCKED.** H-NEG-13 is a known wording the gate passes, so release depends on the NLI. Coverage stays blocked until that is fixed and re-measured on new held-out rows. |
| Clinical validation | None. |

## 1. Starting state

- **C2:** `C:\Users\sunny\r7-c2-gate`, 35/35 fingerprint OK, HEAD `2190fb0`.
- **M1:** the 15 artifacts are fingerprinted (`m1_artifacts_fingerprint.txt`) and all OK at the end.
- **The owner's AI-proposed M1 labels** are saved separately at `C:\Users\sunny\r7-c2b-work\MEDROLE_REVIEW_PACKET_AI_PROPOSED.csv` (`13ded6bf…`). They are not copied into the canonical packet. Agreement with the M1 AI labels is 189/191; the two disagreements are R-017 and R-087. Both label sets are AI-produced, so this agreement is not independent review.
- **C2b copy:** `C:\Users\sunny\r7-c2b-gate`, a `git clone --local` at `2190fb0` (detached, `origin` removed), with the 35 C2 files copied and verified (35 OK). Same 144 Python packages. No `.env`/`.env.local`.

## 2. Held-out set, frozen before any code change

`experiments/round7_medication_role_v2/` was frozen at 10:08:51 +05:30. The manifest records the gate and `live_application.py` hashes at freeze time, which equal C2's, with 0 code changes and 0 gate runs before freezing. A hashed copy is in `C:\Users\sunny\r7-c2b-work\heldout_frozen\`, verified unchanged after the run.

| Item | Hash / count |
|---|---|
| `CRITERIA_V2.md` (V1 verbatim plus additions: anaphors need an antecedent in the same answer; document phrases; effect-first, passive, nested and instruction wordings; held-out rule) | `3105e1a3…0d96` |
| `MEDROLE_HELDOUT_V2.jsonl` | `3f411932…0940`, 119 rows, **all constructed** |
| `review/BLIND_REVIEW_PACKET_V2.csv` (no labels, no gate output) | `168de646…9e56` |

Categories: ordinary 20, compound 10, drug class 10, contextual 10, common word 8, proper noun 8, document subject 8, non-medical 10, anaphor 8, negative 27. The rows use different drugs, invented names (Vexoril, Durapex, Quenzarin, Zelvanex) and new wordings, and none was used during C2b development. No real-model rows: the isolated copies hold no credentials.

## 3. What changed (C2b relative to C2)

| File | Change |
|---|---|
| `verification/medication_role_gate.py` | **Effect first:** "X is associated with / linked to Y"; an effect or comparison word before "with X" ("a known risk with X", "the effect is larger with X", "reported/seen with X"); fronted "With X, …". **Passives:** "triggered / provoked / aggravated / exacerbated … by X". **Nested:** "regimen / therapy includes / containing X", and "alongside / together with / in combination with / combined with" read as separate participants. **Instructions:** "avoid / stop / do not combine / co-prescribing X"; "Concomitant use of X with Y is contraindicated". **Anaphors** resolve only to medications named earlier in the same answer and named by this statement's cited source; a singular anaphor with two referents is ambiguous. **Subject boundary:** a subject stops at a reporting verb before a relativizer ("lists drugs that" → "drugs"; "reported that X" → X). **Document phrases** are recorded and never treated as medications; the medication a document is for is checked (`DOCUMENT_SUBJECT`). The reason wording no longer calls a non-medication "the medication". |
| `services/live_application.py` | Passes the answer's earlier statements to the gate as anaphor context (5 lines). The release invariant (`_releasable` reads the gate record) is unchanged. |
| `tests/e2e/test_medication_role_gate_c2b.py` (new, 23 tests) | The 12 M1 counterexamples: 6 releases, 4 NLI-only misses, C-NEG-12 and C-NEG-21. For each one: the verifier outcome is recorded, the gate role and entity are found and rejected, the answer is withheld, and the source is not marked as support. Also 3 uncited-instruction cases, C-PN-06, and 7 grounded positive controls (including a grounded "this combination" and "it"). |
| `tests/test_medication_role_gate.py` (+11 tests) | Effect-first rows, the anaphor resolution table (7 cases), reporting-verb boundaries (4 cases, including one where a document phrase must not hide an invented drug). |
| **Changed expectations (listed, with reasons)** | (1) **Unit "anaphor":** "This combination …" with no antecedent now expects REJECT (it was PASS in C2), which is the C2b rule. (2) **The C2 "known limits" test** became `test_an_effect_before_the_medication_is_now_read`. (3) **e2e "this combination" control:** now given its antecedent sentence. (4) **`test_live_failure_semantics.py` fixture:** a patient consideration "myopathy risk rises with age" became "clarithromycin raises the risk of myopathy". Under C2b, "with age" is an effect-role entity that this fixture's evidence does not name, so the gate rightly rejects it. The fixture exists to test a fully verified answer, so its text was made grounded; no assertion was weakened. |

Exact diff of the modified files: `C:\Users\sunny\r7-c2b-logs\C2b_vs_C2_modified.diff` (567 lines, `6500636d…`). The frozen fingerprint (44 files) is `c2b_fingerprint.txt` (`199fa234…`). Unchanged: the frontend, data, cache (C1's four mappings), lexicon, prompts, NLI model, trust settings and relationship records.

## 4. The ten M1 failures, now

All ten were run through the live path (scripted generation, scripted over-entailing NLI). For every row the verifier itself released the claim, and the withholding is the identity gate's.

| M1 id | Wording | Gate entity / class | Final |
|---|---|---|---|
| C-NEG-07 | Metamizole is associated with hyperkalemia | Metamizole, UNRESOLVED | withheld |
| C-NEG-08 | Hyperkalemia is a known risk with metamizole | metamizole, UNRESOLVED | withheld |
| C-NEG-09 | With metamizole, potassium levels can rise | metamizole, UNRESOLVED | withheld |
| C-NEG-13 | It can cause hyperkalemia … | It, UNRESOLVED (no antecedent) | withheld |
| C-NEG-14 | This drug can cause hyperkalemia … | This drug, UNRESOLVED | withheld |
| C-NEG-15 | Patients whose regimen includes Zorbitrex alongside lisinopril … | Zorbitrex, UNRESOLVED | withheld |
| C-NEG-10 | Hyperkalemia has been reported with Zorbitrex | Zorbitrex, UNRESOLVED | withheld |
| C-NEG-11 | Hyperkalemia may be triggered by Zorbitrex | Zorbitrex, UNRESOLVED | withheld |
| C-CMP-06 | …, and metamizole is associated with hypotension | clause 2: metamizole | withheld; clause 2 named |
| C-CMP-10 | …, and the effect is larger with Zorbitrex | clause 2: Zorbitrex | withheld; clause 2 named |

**C-PN-06** ("The FDA label for warfarin lists drugs that increase bleeding risk"): the gate **passes**. The document phrase "The FDA label for warfarin" is recorded; "drugs" is the effect subject, named by 7.3; warfarin is the `DOCUMENT_SUBJECT`, grounded. Support remains the verifier's own decision.

**Uncited instructions:** "avoid co-prescribing these medications" (anaphor, no grounding), "Concomitant use of lisinopril with spironolactone is contraindicated" and "Avoid combining lisinopril with Zorbitrex" are all REJECT, with the entity recorded.

## 5. Validation (frozen C2b, 10:36:02 +05:30; logs in `C:\Users\sunny\r7-c2b-logs\`)

| Check | Result |
|---|---|
| Focused: gate unit (45), gate e2e (35), C2b regressions (23), live failure semantics, citation alignment, guard, lexicon, normaliser (C1's 5) | all pass |
| Backend, normal network (`TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false -rfsxX tests`) | **2007 passed, 4 skipped**, exit 0 (10:36:18–10:44:46) |
| Backend, network blocked (proxies to 127.0.0.1:9, HF/Transformers offline, `--offline`) | **2007 passed, 4 skipped**, exit 0 (10:44:46–10:59:11) |
| Count | C2 1977 collected + 34 new = 2011 = 2007 + 4 |
| vitest / `tsc -b` / oxlint | 148/148; exit 0; exit 0 with the same 3 warnings in untouched files |
| ruff (all changed Python) / bandit `-ll` / whitespace | pass / exit 0, no findings / clean |
| gitleaks 8.30.1 `dir --redact` | **no leaks**; scope: copies of the **44 changed files only** (`c2b_files.txt`) |
| Integrity scripts | PASS, PASS, 311 pinned |
| Frozen data | eval set `bd23fe48…`, lexicon `bcf0d184…`, cache `a80146bd…` (C1); protected paths: no diff vs `2190fb0` |
| **Frozen 42-set** (real NLI, rerun) | 9 released, 0 false releases, the same 5 false withholds, gate rejections only on D05, E08 and E27, **no outcome change**. The result file differs in bytes from C2's only in the recorded gate texts. |

The 4 skips are the provider-credential tests (no `.env.local`, deliberately). Not run: browser, real-LLM generation.

## 6. Held-out measurement (real NLI, scripted generation, all 119 rows on the full path)

`results/HELDOUT_RESULTS_V2.jsonl` (`6c43f8bf…`), `results/HELDOUT_METRICS_V2.json` (`b21a9e26…`).

**Metric A, identity false withholds: 1 / 79 (1.3%)**

| Category | False / valid |
|---|---|
| ordinary | **1 / 20** (H-ORD-09) |
| compound | 0 / 4 |
| drug class | 0 / 8 |
| contextual | 0 / 10 |
| common word | 0 / 8 |
| proper noun | 0 / 8 |
| document subject | 0 / 7 |
| non-medical | 0 / 10 |
| anaphor (grounded) | 0 / 4 |

**H-ORD-09:** "A reduced starting dose of lisinopril is advised …". The effect-verb pattern read the adjective "reduced" as a verb, with subject "A". This is a new defect class: a past participle used as an adjective.

**Metric B, unsupported medication claims: 40 tested, 39 rejected by the gate, 1 missed, 0 released**

| Pattern | Tested | Gate rejected | Missed | Released |
|---|---|---|---|---|
| effect first | 7 | 7 | 0 | 0 |
| passive | 5 | 5 | 0 | 0 |
| implicit subject / anaphor | 7 | 7 | 0 | 0 |
| **nested** | 4 | 3 | **1 (H-NEG-13)** | 0 |
| compound (effect-first / nested / passive later clause) | 6 | 6 | 0 | 0 |
| uncited instruction | 4 | 4 | 0 | 0 |
| class named in other words | 3 | 3 | 0 | 0 |
| structured fields | 2 | 2 | 0 | 0 |
| wrong brand / ambiguous | 2 | 2 | 0 | 0 |

**H-NEG-13:** "Patients receiving lisinopril in combination with metamizole may develop hyperkalemia [Source 1]". The exposure phrase is cut at "in" before "in combination with" is read, so metamizole is never seen. The gate passed it; the real NLI did not entail it (0.74, verifier "qualify"), and that alone withheld it. **This is a residual bypass and stays blocking.**

**Metric D:** all 10 compound rows were correct. The 6 invalid ones were rejected, and clause 2 was surfaced as the failing clause.

**Metric E (119 full-path rows):**

| Identity gate | Released | Withheld |
|---|---|---|
| PASS | 45 | 34 |
| REJECT | 0 | 40 |

The 34 withholds of gate-PASS rows are from the verifier (non-entailment or aggregate), pair identity, or the round-6 guard, not from identity.

**Caveats:** the labels are AI-preliminary and written by the implementer; all rows are constructed; the sample is small. These numbers are preliminary engineering evidence.

## 7. Remaining limitations

1. **H-NEG-13**, blocking: "in combination with X" after an exposure verb. It needs the combiner normalisation applied before the phrase is cut.
2. **H-ORD-09:** a participle adjective is read as an effect verb ("A reduced dose").
3. **"With X" agents:** a non-drug "with" qualifier the source does not name ("risk rises with age") is now withheld. This is conservative, and seen once in an existing test fixture.
4. **Bounded patterns:** wordings outside them still have no role. The held-out set found one (item 1).
5. **No real-model rows, no owner labels, no browser run.**

A remediation for items 1 and 2 would be a small candidate (C2c), validated on new held-out rows. Fixing them now, after seeing the held-out results, would make this held-out set no longer held out for those patterns.

## 8. Final state

- **C2b:** `C:\Users\sunny\r7-c2b-gate`, 44-file fingerprint OK, plus the held-out results.
- **Untouched:** C2 (35 OK), C1 (27 OK), M1 artifacts (15 OK), the Round-6 checkout (24 OK, the same 9 tracked changes as before) and the cache-fix worktree.
- **Nothing staged, committed or pushed.**
