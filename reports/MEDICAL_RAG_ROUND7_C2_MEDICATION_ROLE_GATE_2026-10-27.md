# Medical RAG round 7, candidate C2: medication-role identity gate (2026-10-27)

Research prototype. Software tests do not establish clinical correctness, patient safety, regulatory compliance or production readiness. C2 was approved alone. M1 and C3 have not started.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Engineering validation of C2 | **Pass.** Every check run on the frozen C2 state passed (section 6). Browser/UI execution through a live backend was **not** run (section 8). |
| Medication-identity coverage | **BLOCKED (unchanged rule).** P06, P07-single and P08-single are withheld through the real release path, including with the real NLI model. Coverage stays blocked until M1 measures false withholding. Role coverage is bounded (section 7). |
| Evidence-support verification | Unchanged. The gate decides identity only; NLI, citation, strength and alignment still decide support. |
| Research readiness | Not ready (M1, C3 outstanding). |
| Clinical validation | None. |

## 1. Starting point and identity propagation

**C1 checked first, unchanged:** `C:\Users\sunny\r7-c1-cache`, HEAD `2190fb0` detached; C1 diff hash `76155e86…` as reported; the four mappings 6851 / 221124 / 203191 / 203191; both C1 tests present; protected paths no diff; coverage files separate (`LEXICON_COVERAGE_V1.json` `401c7c3f…`, `LEXICON_COVERAGE_C1_CANDIDATE.json` `9bdf87d4…`). The C1 candidate was not modified (27-file fingerprint all OK again at the end).

**Propagation probe** (`C:\Users\sunny\r7-c2-work\probes\test_c1_identity_propagation.py`, run on C1; real live pipeline, real `DrugNormalizer` over the curated cache with no RxNav calls, scripted generation): 4 passed.

| Requested | Normalizer / rxnorm event | Request identity map | Prompt line | Released answer | Lexicon's own identity |
|---|---|---|---|---|---|
| Methotrexate | 6851 (`seed_cache`) | `methotrexate: 6851` | `methotrexate (RxCUI: 6851)` | 6851 | 6851 IN |
| Metoprolol succinate | 221124 | `metoprolol succinate: 221124` | `(RxCUI: 221124)` | 221124 | 221124 PIN |
| Metoprolol tartrate | 203191 | `metoprolol tartrate: 203191` | `(RxCUI: 203191)` | 203191 | 203191 PIN |
| Lopressor | 203191, canonical name metoprolol tartrate | `lopressor` and `metoprolol tartrate`: 203191 | `metoprolol tartrate (RxCUI: 203191)` | 203191 | 203344 BN (brand concept; the cache maps brands to their generic by convention) |

No retired value (7052, 866508, 866514) appears in any prompt. Methotrexate is no longer represented as morphine anywhere on this path.

## 2. Candidate

- **Path:** `C:\Users\sunny\r7-c2-gate`, a separate `git clone --local` at `2190fb0` (detached, `origin` removed), with the 27 C1 files copied from the C1 candidate and verified (27 OK) before any edit. Same 144 Python packages; `npm ci` 141 packages. No `.env`/`.env.local` copied, opened or created. No new package, provider, database or network dependency.
- **Baseline before edits:** focused suites 119 passed, 1 xfailed (as C1).
- **Frozen at 2026-10-27 23:49:49 +05:30:** 35 changed/untracked files, fingerprint `C:\Users\sunny\r7-c2-logs\c2_fingerprint.txt` (SHA-256 `a124d35d…`), all OK after the last run. The replay result written afterwards is the only file added since (an output).

## 3. Gate order traced (before coding), and what changed

Round-6 order for each statement in `live_application.py`:
1. `answer_statements` → `_item_statement` flattens structured items into one sentence (drug fields lost as fields);
2. `ClaimVerifierV2.verify` splits into clauses (`decompose_into_claims`), NLI over all chunks, cited-chunk gate, relationship-scope and pair-identity checks per clause;
3. claim record: support state, and identity copied from the **first** clause with an identity (the compound-claim defect);
4. no citation / invalid citation → UNSUPPORTED;
5. only if still SUPPORTED: strength and source-text checks, citation alignment, round-6 medication guard (each sets UNSUPPORTED);
6. release = every claim's `support_state == SUPPORTED`; evidence marked "supports" from the same field.

**Overwrite points:** steps 3–5 all write the single `support_state` field, and release (6) trusted it; the round-6 guard ran only on claims still SUPPORTED, so it recorded nothing otherwise.

**C2 order:** a new step 0 runs the identity gate for **every** statement before the verifier and writes `claim["identity_gate"]` (initialised to REJECT, so an error fails closed). Steps 1–5 are unchanged. A rejected claim is also shown UNSUPPORTED. Release (6) and the evidence marking now use `_releasable(claim)`: `support_state == SUPPORTED` **and** `identity_gate.decision == "PASS"` **and** no round-6 `medication_identity` finding, read from their own records.

## 4. Changed files (C2 relative to C1)

| File | Change |
|---|---|
| `src/.../verification/medication_role_gate.py` (new, 307 lines) | Role patterns, identity classes, `identity_gate()` |
| `src/.../services/live_application.py` (+/−90 diff lines) | `AnswerStatement.roles` from drug fields; gate call before the verifier; `_releasable`; `_clause_judgments`; summary identity from the first failing clause; `failed_clause`; abstention-reason sentence |
| `frontend/src/components/ResultPanel.tsx`, `frontend/src/types/index.ts` | Reason line for a gate rejection (with its clause) and for a compound claim's failing clause |
| `tests/test_medication_role_gate.py` (new, 34 tests), `tests/e2e/test_medication_role_gate.py` (new, 30 tests), `frontend/src/components/ResultPanel.test.tsx` (+3 tests) | Section 5 |
| `tests/e2e/test_citation_alignment.py` | The metamizole strict xfail became a normal test with stronger assertions |
| `tests/e2e/test_live_failure_semantics.py` | **Changed expectation (1 test):** an uncited interaction statement's abstention reason now has one more sentence, because its participants are not named by any cited source and the gate rejects it too. The claim was already withheld; the earlier sentences are unchanged. |
| `experiments/round7_c2/replay_c2.py` (new) | Runs the round-6 replay unchanged, writes to its own results file, adds each claim's gate record |

Exact diff of the modified files against C1: `C:\Users\sunny\r7-c2-logs\diff\C2_vs_C1_modified.diff` (SHA-256 `c6c377b3…`). Data, cache, lexicon, prompts, NLI model and revision, trust formula, weights, thresholds, eligibility and the citation requirement: no change.

**Root cause addressed (P07/P08):** no check saw "Metamizole" or "Zorbitrex" because recognition depended on the lexicon or a drug-name suffix. The gate looks at the **role**: the subject of "can cause hyperkalemia" is checked whatever the name. It is not confirmed, not in the lexicon, and §7.1 does not name it, so it is `UNRESOLVED` and the claim is rejected, independent of the NLI's 0.98.

## 5. Results by case

**Scripted generation, real live path, scripted over-entailing NLI** (`tests/e2e/test_medication_role_gate.py`; every case also asserts the verifier itself released the claim, so the withholding is the gate's):

| Case | Retrieved | Result | Gate class |
|---|---|---|---|
| P06 furosemide → 7.1 | 5.5 + 7.1 | withheld | `CANONICAL_RESOLVED`, not named (round-6 guard also fires) |
| P06-single | 7.1 | withheld | same |
| P07 metamizole | 5.5 + 7.1 | withheld | `UNRESOLVED` |
| **P07-single** | 7.1 | **withheld** | `UNRESOLVED` |
| P08 Zorbitrex | 5.5 + 7.1 | withheld | `UNRESOLVED` |
| **P08-single** | 7.1 | **withheld** | `UNRESOLVED` |
| P09-single dipyrone | 7.1 | withheld | `CANONICAL_RESOLVED`, not named |
| P01 enalapril | 5.5 + 7.1 | withheld | `CANONICAL_RESOLVED`, not named |

All rejected cases: evidence never marked as supporting a verified claim.

**Positive controls** (same harness): released with gate PASS: source-grounded lisinopril (5.5); "ACE inhibitors such as lisinopril" (`MEMBER_GROUNDED` via lisinopril); "Potassium-sparing diuretics such as spironolactone" (7.1); an exposure statement ("patients receiving lisinopril"). Gate PASS and no medication finding: "In the ALLHAT trial cohort …", "The Mayo Clinic recommends …" (no drug role), "Renal insufficiency can increase …" (`NON_DRUG_NAMED`, named by 5.5), "This combination can increase …" (`ANAPHOR`), lower-case "react". Common-word collision "air": the gate does not examine it (no role); the **round-6 guard still withholds it** because 5.5 does not name "air", which is the approved round-6 fail-safe behaviour, kept.

**Structured roles** (live path): adverse reaction, interaction and administration items naming Lisinopril / Spironolactone pass the gate in their field role; "Zorbitrex" in each of the three fields is rejected `UNRESOLVED` with `failed_clause = "field <ROLE>"`; "Camphor" (an ambiguous lexicon span) in `adverse_reactions.drug` is rejected `AMBIGUOUS`. A source-named name outside the lexicon (`SOURCE_NAMED_UNRESOLVED`, RxCUI null) is tested at unit level with a synthetic cited string, because no approved fixture names such a drug. The schema has **no structured dosage field**; dosage is covered in free text ("dose of X", "X should be taken").

**Monotonicity:** with the strength, source-text, alignment and round-6 checks all patched to "no problem" and the verifier summary patched to SUPPORTED, P08-single is still withheld and its evidence is not marked as support. `_releasable` is unit-tested: SUPPORTED + REJECT → not releasable; missing gate record → not releasable. A gate exception fails closed.

**Compound claims:** "Lisinopril can cause hyperkalemia, and Zorbitrex can cause hypotension [Source 1]." → clause 1 PASS, clause 2 REJECT, `failed_clause` is clause 2. "Lisinopril interacts with spironolactone, and spironolactone increases lisinopril exposure [Source 2]." → `clause_judgments` = [MATCH, not MATCH]; the claim's summary `canonical_identity_status` is the failing clause's (round 6 showed MATCH), and `failed_clause` carries that clause and its reason. UI (vitest): the gate reason is shown with the quoted clause; a structured-field rejection is shown without a clause; a compound claim with a passing summary now shows `Clause "<failing clause>": <reason>` instead of no reason.

**Real-model replay** (`experiments/round7_c2/results/LIVE_POLICY_REPLAY_C2.json`; pinned `pritamdeka/PubMedBERT-MNLI-MedNLI@f1b6ce2e…`, real DailyMed sections, every live gate; **generation scripted**, real model for NLI only):

| | Round 6 (frozen file) | C2 |
|---|---|---|
| Frozen 42-set (`bd23fe48…`): released | 9 | 9 |
| False releases | none | none |
| False withholds | D02, E06, E07, E09, E10 | the same 5 |
| Outcome changes | — | **none** |
| P07-single (entailment 0.981, verifier released) | RELEASED | **WITHHELD** (gate) |
| P08-single (0.986, verifier released) | RELEASED | **WITHHELD** (gate) |
| P06/P06-single/P09-single/P01 | withheld | withheld (gate and round-6 guard) |

The gate also rejects 3 frozen-set examples that were already withheld and are labelled WITHHOLD: D05 (acetaminophen cited to a warfarin section that does not name it), E08 ("thiazide-type diuretics" cited to 5.5, which does not name them), E27 (amlodipine). None changed outcome. The round-5 harness's `withheld_by` labels P07/P08-single "verifier: aggregate state UNSUPPORTED" because it reads `support_state`; the record shows `verifier_decision: release` and gate REJECT, so the withholding is the gate's.

## 6. Validation (frozen C2 state; logs in `C:\Users\sunny\r7-c2-logs\`)

| Check | Result |
|---|---|
| Focused: gate unit (34), gate e2e (30), citation alignment, guard, lexicon, inventory, normalizer (incl. C1's 5) | all pass; **0 xfail** (the metamizole test now passes as a normal test) |
| Backend, normal network: `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false -rfsxX tests` | **1973 passed, 4 skipped**, exit 0 (23:50:00–23:52:30) |
| Backend, network blocked (proxies to 127.0.0.1:9, HF/Transformers offline, `uv run --offline`) | **1973 passed, 4 skipped**, exit 0 (23:52:30–23:56:12) |
| Count check | C1 1913 collected + 64 new = 1977 = 1973 + 4 |
| vitest | **148/148** (22 files) |
| `tsc -b` | exit 0 |
| oxlint | exit 0; the same 3 warnings in untouched files |
| ruff (all 17 changed Python files) | all checks passed |
| bandit `-q -ll` (changed source, new module, build script, round-6 and round-7 experiment folders) | exit 0, no findings |
| Whitespace (`git diff --check`; `--no-index --check` per untracked file) | clean |
| gitleaks 8.30.1 `dir --redact` | **no leaks**; scope: copies of the **35 changed files only** (list in `c2_files.txt`), not the repository |
| Integrity scripts | PASS, PASS, 311 pinned / 0 unpinned |
| Frozen data | eval set `bd23fe48…` unchanged; lexicon `bcf0d184…`; round-6 replay and coverage files unchanged; protected paths (eval set, prompts, `data/live_medical`, `data/evidence`, trust scoring, verifier, LLM backend, fixtures, config) no diff vs `2190fb0`; cache = C1's |

**The 4 skips** are the provider-credential tests, which need `.env.local`; it was deliberately not copied. **Distinction:** unit tests are deterministic; the e2e tests run the real live path with scripted generation and a scripted NLI; the replay uses the real NLI model with scripted generation. No real-LLM generation and no browser were used for C2.

## 7. Coverage limits (not hidden)

Recognised roles: effect subject ("X can cause / increase / reduce / lead to …"), interaction ("X interacts with Y", "X is contraindicated with Y", "use of X and Y"), agent ("caused by X", "X-induced"), exposure ("patients taking / receiving / on X"), dosage ("dose of X", "X should be taken"), and the three schema drug fields.

Known gaps, each pinned by a test so they stay visible:
- **Effect before the medication:** "Hyperkalemia is a known risk with metamizole", "With metamizole, potassium levels can rise", "Metamizole is associated with hyperkalemia" get **no role**, so an unresolved name in them is **still releasable** if the NLI entails it (the round-6 guard does not see names outside the lexicon). "Reports of hyperkalemia in patients on metamizole therapy" **is** caught (exposure role).
- **Passives** other than "caused / induced / precipitated by X" are not read.
- **Implicit subjects** ("It can cause …") pass as anaphors; the gate cannot check what they refer to.
- **Effect-subject and agent roles cannot tell** a non-lexicon medication from a non-drug subject; both pass only if the cited source names them word for word. A non-drug subject the source does not name ("Smoking can increase …") is withheld (conservative).
- **Pure class subjects** the source does not name word for word are withheld (no class vocabulary, as designed).
- **Complex sentences:** roles are read per sentence and recorded on the verifier clause containing the entity; very long or nested sentences can be cut wrongly by the bounded patterns.

M1 must count releases in these forms; P07/P08 passing does not close the safety problem.

## 8. Not performed

- **Browser/UI run through a live backend.** The round-6 scripted-generation harness (`run_backend_probe.py`) was not found on this PC, and a new backend harness was out of C2's scope. The UI reason lines are covered by vitest only.
- **Real-LLM generation** for C2 (generation was scripted throughout).
- **Fresh clone of a commit** (nothing is committed; the isolated clone reproduces the exact uncommitted state by fingerprint instead).
- M1 and C3: not started.

## 9. Final state

- **C2:** `C:\Users\sunny\r7-c2-gate`, HEAD `2190fb0` detached, 35 changed/untracked files (fingerprint OK) plus the replay result; nothing staged or committed.
- **C1:** unchanged (27-file fingerprint OK).
- **Round-6 checkout:** HEAD `2190fb0`, 24-file fingerprint OK, no tracked change; the only new files are reports (these round-7 reports, and a food-guidance report from another thread).
- **Cache-fix worktree:** untouched. Nothing pushed anywhere.

Stopped after C2. M1 and C3 each need separate approval. Medication-identity coverage stays **BLOCKED** until M1 is done.
