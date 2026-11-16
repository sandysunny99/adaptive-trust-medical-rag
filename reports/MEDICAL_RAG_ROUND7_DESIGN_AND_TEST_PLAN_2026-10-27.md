# Medical RAG round 7: state reconciliation, medication-role gate design, relationship-effect analysis (2026-10-27)

Research prototype. Nothing in this document is a clinical claim. **No code, data, test, prompt, model setting or threshold was changed for this document.** It covers execution steps 1 to 5 of the owner's Round 6 decisions. Step 6 (implementation candidates) has not started and waits for the owner's go-ahead on each candidate.

## 0. Status, kept separate

| Category | Status |
|---|---|
| Engineering validation | Round-6 candidate (01:28:03) unchanged and fingerprint-verified today. No new runs this round. Fresh clone still not run. |
| Medication-identity coverage | **BLOCKED.** P07-single (metamizole) and P08-single ("Zorbitrex") are still released as verified. Design below; not implemented. |
| Evidence-support verification | Unchanged. The E28 class-to-specific pattern is still possible wherever a relationship record is approved. Design below; not implemented. |
| Research readiness | Not ready. The false-withhold measurement (section 4.4) has not been run. |
| Clinical validation | None. No clinician review. |

## 1. Step 1: both worktrees, and the conflicting commit reports

**Round-6 checkout** `C:\Users\sunny\Downloads\CASE STUDY`
- Branch `wip/pre-threads-20261022-1440`, HEAD `2190fb0`. Nothing staged.
- `sha256sum -c` against the Round-6 candidate fingerprint (`r6c_fingerprint.txt`, 01:28:03): **all 24 files OK**. The working tree is exactly the validated candidate.
- `data/drug_entity_cache.json` and `tests/test_drug_normalizer.py` are unmodified (blobs `9efd807` and `4617b9b`).

**Cache-fix worktree** `.claude/worktrees/zealous-curran-3c90b2`
- Branch `claude/zealous-curran-3c90b2`, HEAD **`b3a3d3e`** "fix(normalization): correct four wrong RxCUIs in the curated drug cache", dated 2026-10-27 11:12 +05:30. Working tree **clean**.
- The branch was cut from `395c214` (GitHub `main`), **not** from `2190fb0`. It does not contain rounds 2 to 6.
- The commit touches 2 files: `data/drug_entity_cache.json` (the 4 approved mappings, 8 lines) and `tests/test_drug_normalizer.py` (+42/-1).

**Reconciliation.** The Round-6 report (section 11) said the cache fix was "on its own branch, none of it in this checkout". The memory note said "a separate session handles it". Both are consistent with what is on disk: **the cache fix is committed as `b3a3d3e` on its own branch, and is not in the Round-6 checkout.** Nothing was pushed (no upstream).

## 2. Step 2: Round-6 evidence preserved

Copied, not moved, to `C:\Users\sunny\round6-evidence-2026-10-27\` (outside the repository), with `SHA256SUMS.txt` over every file:
- `candidate_tree/`: the 24 candidate files byte for byte;
- `round6_tracked_changes_vs_2190fb0.patch`: the 6 modified tracked files as a diff;
- `validation_logs/`: both fingerprints, the file list, backend and network-blocked logs (baseline and candidate), the real-model replay logs, and the pre-audit status;
- `probe_tests/`: the three scratch probe tests;
- `MEDICAL_RAG_ROUND6_MEDICATION_LEXICON_REPORT_2026-10-27.md`, `HEAD.txt`, `git_status_2026-10-27.txt`.

**Gap:** the browser probe harness (`run_backend_probe.py`, `probe_mode.txt`) named in Round 6 was **not found** anywhere under the user profile. The UI reproduction of P07/P08 is documented in the Round-6 report but cannot be re-run from that harness. Any future UI reproduction needs a new harness.

Frozen baseline (01:12:06) and candidate (01:28:03) results remain separate files (`r6_*` and `r6c_*`).

## 3. Step 3: medication-role identity gate (Decision 1), design

### 3.1 Why P07/P08 pass today

- `medication_identity_violation` only sees names found by the RxNorm lexicon or by `drug_mentions` (a fixed list and seven suffixes). "Metamizole" and "Zorbitrex" match neither, so the guard sees no medication.
- With only §7.1 retrieved, the alignment screen has no other section to compare against, and the NLI entails at 0.98.
- The guard also runs only **after** the verifier said SUPPORTED, inside the same branch as the strength checks, so its result is mixed into `support_state` rather than recorded as its own decision.

### 3.2 Principle

An entity is checked because of the **role** it plays in a claim about drug effects, not because its name is unfamiliar. Unfamiliar words outside such a role are never examined. Inside such a role, an entity must have an identity that is either resolved or grounded in the cited source. Identity never counts as evidence support: NLI, citation, strength and alignment still decide support.

### 3.3 Where roles come from

**Structured fields (exact).** `AnswerStatement` gains a `roles` tuple, filled in `_item_statement` from the item itself, before the text is flattened:
- `interactions[i].drug_a`, `drug_b`: role INTERACTION_PARTICIPANT;
- `adverse_reactions[i].drug`: role ADVERSE_EFFECT_SUBJECT;
- `food_guidance[i].drug`: role ADMINISTRATION_SUBJECT.

**Free text** (conclusion sentences, `warnings`, `claims_for_verification`, `patient_considerations.consideration`). Roles are read per clause, using the verifier's own `decompose_into_claims` split, so a clause record lines up with a verifier judgment. A bounded, documented pattern set:

| Role | Pattern (case-insensitive, whole words) | Entity span |
|---|---|---|
| Effect subject | `<NP> [can/may/might/could/will/does/is known to] cause(s) / induce(s) / increase(s) / decrease(s) / raise(s) / lower(s) / reduce(s) / potentiate(s) / inhibit(s) / lead(s) to / result(s) in / produce(s) / worsen(s)` | the clause-initial NP |
| Interaction | `<NP> interact(s) with <NP>`; `<NP> is/are contraindicated with <NP>`; `(concomitant / co-) (use / administration / combination) of <NP> (and/with) <NP>`; `taking <NP> with <NP>` | both NPs |
| Agent | `<effect> (caused / induced) by <NP>`; `<NP>-induced <effect>`; `associated with <NP> (use/therapy)` | the NP |
| Exposure | `(patients / people / those / individuals) (taking / receiving / on / treated with / using) <NP>` | the NP |
| Dosage | `(dose / dosage / dosing) of <NP>`; `<NP> should be (dosed / taken / given / started)` | the NP |

`<NP>` stops at the predicate, a comma, a `[Source N]` marker or a preposition other than "such as". Leading determiners are dropped. A clause with no pattern has **no role** and is not examined by this gate (Round-6 behaviour for contextual mentions is kept, section 3.5).

**Anaphors** ("it", "this", "these", "both", "the combination", "this medication", "such agents", "the drug") in a role assert no new identity. They get outcome `ANAPHOR` and pass this gate. The verifier still has to support the clause.

### 3.4 Identity classes for an entity in a role

Exact matching only. No approximate matching, no stemming of drug names, no synonyms, and no RxCUI is ever invented.

| Class | Test | Gate outcome in a role |
|---|---|---|
| `CANONICAL_RESOLVED` | one lexicon concept on the span (RxCUI, TTY) | pass **if** a cited source names it (Round-6 rule); else reject "not named by its cited source" |
| `USER_CONFIRMED` | the request's confirmed medication (name or RxCUI in `RequestDrugMap`) | pass if a cited source names it; else reject "confirmed medication its cited source does not mention" (P01, P06 path unchanged) |
| `SOURCE_NAMED_UNRESOLVED` | not in the lexicon, not confirmed, but a cited source names the exact span | pass for identity, recorded with `rxcui: null`. Support is still decided by the verifier. |
| `AMBIGUOUS` | two or more lexicon concepts on the span | reject "ambiguous medication identity" (never guessed) |
| `UNRESOLVED` | none of the above | **reject** "names X as the medication in a drug-effect claim, but X has no resolved identity and the cited source does not name it" |
| `MEMBER_GROUNDED` | the NP contains medication mentions, every one of them passes, e.g. "ACE inhibitors such as lisinopril" | pass; the class words are left to the verifier |
| `NON_DRUG_NAMED` | the NP contains no medication mention and every content word is named by a cited source, e.g. "Renal insufficiency can cause hyperkalemia" | pass |

P07-single: the subject "Metamizole" is not in the lexicon, not confirmed, and §7.1 does not name it, so it is `UNRESOLVED` and rejected. P08-single: the same with "Zorbitrex". P06: furosemide is `CANONICAL_RESOLVED` (RxCUI 4603), unconfirmed, and not named by §7.1, so it is rejected as today.

### 3.5 Mentions outside any role

They keep the Round-6 rule exactly: a medication the lexicon or `drug_mentions` finds must be named by a cited source. This keeps "Serum potassium should be monitored" and the §7.1 contextual spironolactone mention passing, and keeps every Round-6 withhold.

### 3.6 Separation and "nothing restores a rejection"

- The gate runs for **every** statement, before and independent of the verifier. It writes its own record, `claim["identity_gate"] = {"decision": "PASS" | "REJECT", "clauses": [...]}`.
- The release decision becomes `all(support_state == SUPPORTED) and not any(identity_gate.decision == REJECT)`. It reads the gate record directly, so no later stage (strength, alignment, NLI, relationship checks, a future change) can turn a rejected claim back into a released one by setting `support_state`.
- A rejected claim also sets `support_state = UNSUPPORTED` for display, and its sources are never marked "Supports a verified claim".
- Fail closed: a missing or altered lexicon rejects every statement (unchanged).

### 3.7 Audit record per clause (and the compound-claim fix)

Each entry in `identity_gate.clauses` holds the clause text, each role entity (span, role, class, RxCUI or null, named-by-cited-source) and the reason if rejected.

Separately, the verifier-identity copy is fixed. Today the claim record takes `canonical_identity_status/reason` from the **first** judgment that has one, so a compound claim whose first clause is `MATCH` and second clause is `UNAVAILABLE` shows `MATCH` and no reason. The record will:
- take the status and reason from the **first failing** clause (falling back to the first clause only when none fails);
- add `clause_judgments`: clause text, support state, identity status, identity reason and relationship scope for every clause;
- surface the failed clause and reason as the UI's reason line.

### 3.8 Deliberately not in scope

- No synonyms, no foreign names, no online RxNorm approximate lookup (Round-6 options a and b). They would need a licence review and their own design.
- No drug-class vocabulary. A pure class subject the cited source does not name ("NSAIDs can increase bleeding risk" cited to a section that says "Nonsteroidal Anti-Inflammatory Agents") **is withheld** under this design. This is conservative and is measured as its own category (4.4). Adding a reviewed class-term list would be a separate owner decision.
- The Security panel's input-side injection count (audit finding) is untouched.

### 3.9 Known limits

- Patterns are bounded. A drug-effect claim phrased outside them ("Hyperkalemia is a known risk with metamizole") has no role and falls back to the Round-6 rule, which does not see unknown names. The measurement in 4.4 counts these as **unsupported medication claims released**, so the gap is reported, not hidden.
- A non-drug causal subject the cited source does not name ("Smoking increases the risk ...") is withheld. That is a citation that does not name its subject, so withholding is defensible, but it is counted in the false-withhold measurement.

## 4. Test plan for Decision 1 (written before any implementation)

### 4.1 Acceptance regressions (live path, scripted over-entailing NLI, as in Round 6)

| ID | Statement | Retrieved | Expected |
|---|---|---|---|
| P06 | "Furosemide can cause hyperkalemia in patients with renal insufficiency [Source 2]" | 5.5 + 7.1 | withheld, `identity_gate` REJECT, class `CANONICAL_RESOLVED` not named by source |
| P06-single | same | 7.1 | withheld, same |
| P07-single | "Metamizole can cause hyperkalemia ... [Source 1]" | 7.1 | withheld, REJECT `UNRESOLVED`. The current strict xfail becomes a normal test. |
| P08-single | "Zorbitrex can cause hyperkalemia ... [Source 1]" | 7.1 | withheld, REJECT `UNRESOLVED` |
| P07, P08 | same | 5.5 + 7.1 | withheld by the identity gate (no longer only incidentally by the aggregate) |
| P09-single | dipyrone | 7.1 | withheld (unchanged) |
| P01 | enalapril → 5.5 | 5.5 + 7.1 | withheld (unchanged) |

### 4.2 Positive controls (must stay released under the same scripted NLI)

- "Lisinopril can cause hyperkalemia [Source 1]" (E25 supported form).
- Drug class with member: "ACE inhibitors such as lisinopril can cause hyperkalemia [Source 1]".
- Contextual medication: "Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia [Source 2]".
- Unfamiliar proper noun **outside** a role: "In the ALLHAT trial cohort, serum potassium was monitored in patients receiving lisinopril [Source 1]".
- Unfamiliar proper noun in a non-drug-effect clause: "The Mayo Clinic recommends monitoring serum potassium [Source 1]" (no role pattern).
- Non-drug causal subject named by the source: "Renal insufficiency can increase the risk of hyperkalemia [Source 1]".
- Common-word collisions ("air", "React") outside a role.
- Anaphor: "This combination can increase the risk of hyperkalemia [Source 2]".

### 4.3 Unit and monotonicity tests

- Role extraction table: each pattern in 3.3, each stop rule, anaphors, clauses split as the verifier splits them.
- Identity class table: one case per class in 3.4, including `AMBIGUOUS` (a stereoisomer span) and `SOURCE_NAMED_UNRESOLVED` (a synthetic cited chunk that names "metamizole").
- Structured roles: an `adverse_reactions` item with `drug: "Zorbitrex"` is rejected; with `drug: "Lisinopril"` cited to 5.5 passes the gate.
- Compound claim: first clause `MATCH`, second `UNAVAILABLE`; the record shows the second clause and its reason, and `clause_judgments` has both.
- **No restore:** monkeypatch every downstream check (verifier, strength, alignment) to "supported"; a gate-rejected claim still abstains, and its source is not marked as support. A test also asserts the release expression reads `identity_gate`.
- Lexicon unavailable: every statement rejected (unchanged).
- Research callers (plain `dict` map) unchanged: the existing research-verifier tests must pass byte for byte.

### 4.4 False-withhold measurement (preliminary engineering evidence)

- **Separate sample:** `experiments/round7_medication_role/MEDROLE_SAMPLE_V1.jsonl`, never mixed with `NLI_EVAL_SET_V1` (hash `bd23fe48…`, labels untouched).
- **Source of claims:** real model statements. First the ones already recorded from real runs (the 30 claims of the Round-6 browser runs, and earlier run folders under `reports/live_validation/runs/`), then new real runs through the live app for a fixed, pre-listed set of medication queries. Constructed rows are allowed only for a category the real outputs do not cover, and each such row is flagged `origin: constructed`.
- **Categories and minimum counts:** ordinary medication claims 20; compound claims 10; drug-class statements 10; contextual medication mentions 10; common-word collisions 8; unfamiliar proper nouns 8; valid non-medical statements 10; and a negative set of unsupported or wrong-identity medication claims 15 (P06 to P09 variants, invented names).
- **Criteria fixed first.** `CRITERIA_V1.md` defines "valid for identity" (every entity in a drug-effect role is the intended entity and the cited source names it or it is the confirmed medication) and is hashed into the sample manifest **before** the gate is run on any row.
- **Labelling:** blind stage first (the label without the gate's outcome), then adjudication, as in the round-5 review packet. AI pre-labels stay in their own column. The owner is the available reviewer. Unless a qualified clinical reviewer labels it, the result is reported as **preliminary engineering evidence**, not a validated dataset.
- **Reported:** valid claims reviewed; incorrectly withheld; false-withhold rate with its denominator; results by category; unsupported medication claims released; ambiguous cases handled conservatively; limitations (sample size, single non-clinical reviewer, pattern coverage).
- **Completion rule:** the fix is not complete when P07 and P08 pass. All 4.2 controls must pass and the measurement must be reported.

## 5. Step 4: relationship-effect scope (Decision 3)

### 5.1 Audit of every relationship record (before any schema change)

No record is approved today. `data/live_medical/relationships/` holds V1 only, with status `CANDIDATE_PENDING_RESEARCHER_APPROVAL`. Severity `UNGRADED` is also rejected by the loader. In the shipped configuration, therefore, no pairwise claim can get a relationship identity, and E28 occurs only where tests approve a copy with a test-only severity.

| Record | Pair, predicate | Where | Evidence span | Effects the span states, and for whom | Supportable from existing evidence? |
|---|---|---|---|---|---|
| REL-LIVE-0001 | simvastatin, clarithromycin; CONTRAINDICATION, A_TO_B, CONTRAINDICATED | `data/` V1, pending | synthetic chunk with a placeholder URL | "increased risk of myopathy and rhabdomyolysis", stated for strong CYP3A4 inhibitors, with clarithromycin **listed** | No. The 2026-10-14 review already recommends not approving V1 (the chunk is not a verbatim label excerpt). Manual review only after a byte-exact recapture. |
| REL-LIVE-0002 | (V2 candidate) | a run folder outside the repo | — | not audited | Not in this repository, so it could not be audited here. |
| REL-LIVE-0003 | lisinopril, spironolactone; INTERACTION, BIDIRECTIONAL, UNGRADED | test fixture, pending | **all of §7.1** | (a) "Potassium-sparing diuretics (spironolactone, amiloride, triamterene, and others) can increase the risk of hyperkalemia": class with spironolactone **listed**. (b) "Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood pressure": diuretics as a class, spironolactone **not named** in that sentence (the E28 pattern). (c) "Lisinopril attenuates potassium loss caused by thiazide-type diuretics": not about spironolactone. | (a) a candidate effect for manual review. (b) and (c) **not supportable** for this pair. |
| REL-LIVE-0004 | warfarin, ibuprofen; INTERACTION, BIDIRECTIONAL, UNGRADED | test fixture, pending | §7.3 and Table 3 | "bleeding risk is increased when these drugs are used concomitantly with warfarin", with ibuprofen **listed** under NSAIDs | A candidate effect for manual review. **Stays UNGRADED**; recording an effect is not a severity grade and does not approve the record. |

### 5.2 Proposed schema (V2.1, additive)

Each record gains:

```json
"effect_scope": "SPECIFIED" | "UNSPECIFIED",
"effects": [{
  "effect_id": "REL-LIVE-0003-E1",
  "effect_term": "hyperkalemia",
  "effect_span": "<verbatim sentence inside evidence_span>",
  "scope": "DRUG_SPECIFIC" | "CLASS_LISTED_MEMBER" | "CLASS_UNLISTED_MEMBER",
  "class_term": "Potassium-sparing diuretics" | null,
  "population": "<verbatim qualifier>" | null,
  "review_status": "PROPOSED" | "APPROVED"
}]
```

Loader validation: `effect_span` is verbatim inside `evidence_span` and the chunk; `effect_term` is a whole-word phrase of `effect_span`; for `DRUG_SPECIFIC` and `CLASS_LISTED_MEMBER` the span names **both** medications (the member explicitly); `CLASS_UNLISTED_MEMBER` is recordable as a review result but **can never support** a drug-specific claim. A record whose manifest is approved still uses only effects with `review_status: APPROVED`.

### 5.3 Matching rule (live path only; research verifier unchanged)

- The claim's effect phrases come from the structured `potential_effect` and `interaction_type`, and in free text from what follows the predicate ("increase the risk of X", "may cause X", "result in X").
- Once `compare_identity` is `MATCH`, a new `compare_effect` step runs:
  - **No effect in the claim** ("lisinopril interacts with spironolactone [Source 2]"): MATCH, as today.
  - **An effect, and the record is `UNSPECIFIED` or has no approved effect:** `AMBIGUOUS`, "the relationship record does not establish this effect". The clause is unsupported. This is the default for every current record, so **an underspecified record never supports a specific outcome**.
  - **An effect matching an approved effect:** the effect phrase's content words must all appear in that effect's `effect_span` (exact, folded). Then MATCH; support is still the NLI's decision.
  - **`CLASS_UNLISTED_MEMBER` only:** `MISMATCH`, "class-level warning; this medication is not named".
- Compound claims are evaluated clause by clause (3.7). One clause failing withholds the claim and names that clause.
- No outcome is ever inferred from a predicate label, a section title or a class warning.

### 5.4 Migration plan

1. Loader accepts V2 (no effect fields, read as `UNSPECIFIED`) and V2.1. Nothing in `data/` changes. Frozen evidence, prompts, model config and trust thresholds stay as they are.
2. Behaviour change: an effect-bearing pairwise claim against a V2 record is withheld where it was previously matched. In the shipped configuration nothing changes, because no record is approved. The tests that approve candidate copies (for example `test_live_warfarin_ibuprofen.py`, `test_live_multi_dataset_loading.py`) are inventoried at implementation time. Each changed expectation is listed in the candidate report, none silently rewritten.
3. Effect data is **not populated**. A proposals file (`experiments/round7_relationship_effect/EFFECT_PROPOSALS_V1.json`, all `PROPOSED`) lists 5.1's candidate effects with verbatim spans for the owner's manual review. Records reach `APPROVED` effects only through the owner's review and a new manifest hash.

### 5.5 Regression tests

- E28: "Initiating lisinopril in patients taking spironolactone may cause excessive reduction of blood pressure [Source 2]" against a test-approved 0003 copy: withheld, `CLASS_UNLISTED_MEMBER` or `UNSPECIFIED`.
- Valid class-level claim with listed member and an approved test effect: "Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia [Source 2]": released.
- Compound: "lisinopril interacts with spironolactone; hyperkalemia; excessive reduction of blood pressure [Source 2]": withheld, naming the blood-pressure clause.
- Unrelated effect: "... interact, causing hepatotoxicity": withheld.
- Missing scope: the same record without effect fields: an effect-bearing claim is withheld, a no-effect claim is unchanged.
- Loader: a non-verbatim `effect_span`, a member not named, `CLASS_UNLISTED_MEMBER` used as support, `PROPOSED` effects ignored.

## 6. Step 5: cache corrections, exact integration diff (nothing applied)

- **Diff:** `git format-patch -1 b3a3d3e`, saved as `C:\Users\sunny\round6-evidence-2026-10-27\cache-fix-b3a3d3e.INTEGRATION.patch` (SHA-256 `49d89c5a…dccbba`).
- **Target check:** both files in the Round-6 checkout are the same blobs as at `395c214`, the commit's parent. `git apply --check` against the Round-6 working tree **passes with no conflict**. The patch was only checked, never applied.
- **Content:** exactly the four approved mappings (methotrexate 7052→6851; metoprolol succinate 866508→221124; metoprolol tartrate 866514→203191; lopressor 866514→203191), schema unchanged, the other 22 entries untouched. The new tests pin each mapping and reject the retired values under any key.
- **Side effects to expect on integration:** the Round-6 coverage result `LEXICON_COVERAGE_V1.json` records the old cache values as findings. It is a frozen baseline result and is not regenerated in place; a candidate run would write a new file.

## 7. Proposed candidates (each starts only after the owner's OK)

**How candidates are built (recommended):** never in the Round-6 checkout. Each candidate is an isolated local copy: a `git clone --local` of this repository checked out at `2190fb0` (detached), plus the 24 Round-6 files copied in and verified against `r6c_fingerprint.txt`, plus that candidate's own diff. This leaves the Round-6 working tree, branch and index untouched. It also answers Decision 4's fresh-clone question: the copy reproduces the exact uncommitted candidate, verified by fingerprint, without a commit. Tests in each copy: backend and network-blocked suites, vitest, `tsc -b`, oxlint, ruff, bandit, scoped gitleaks, integrity scripts, frozen-set hash.

| Candidate | Diff | Done when |
|---|---|---|
| **C1 cache corrections** | the patch in section 6, applied in the copy | the full suites pass; `test_drug_normalizer` pins the 4 values; 22 entries byte-identical |
| **C2 medication-role gate** | sections 3 and 4.1 to 4.3, plus the compound-claim record fix | P07/P08-single withheld; all 4.2 controls released; monotonicity tests pass; frozen 42-set outcome reported unchanged or every difference explained |
| **M1 false-withhold measurement** | section 4.4, on C2 | criteria hashed first; numbers reported as preliminary engineering evidence |
| **C3 relationship-effect scope** | section 5 code and tests; proposals file only, no data populated | the 5.5 tests pass; every changed test expectation listed |

Medication-identity coverage stays **BLOCKED** until C2 and M1 are both done.
