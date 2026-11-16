# Medical RAG round 7, M1: false-withhold and residual-bypass measurement of the C2 gate (2026-10-28)

Research prototype. **Preliminary engineering evidence, not clinical validation.** Every label in this report is an AI-preliminary label, written from frozen criteria by the same assistant that implemented C2; the owner's blind review has not been done yet. No clinician has reviewed anything. M1 changed no gate code; C3 has not started.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Identity false withholding (C2 gate) | **Low on this sample:** 1 of 87 cited valid-identity rows (1.1%). One real defect pattern (section 4). |
| Residual unsupported releases | **BLOCKING:** **6 of 32** full-path negative rows were **released as verified**: 3 effect-before-drug, 2 implicit-subject, 1 nested. 3 more were missed by the gate and stopped only by the NLI or the round-6 guard. |
| Medication-identity coverage | **BLOCKED.** Known wordings still release unsupported medication claims. |
| Evidence-support verification | Unchanged; reported separately (metric E). |
| Clinical validation | None. |

## 1. Candidate and preserved state

- **C2 recorded first:** `C:\Users\sunny\r7-c2-gate`, HEAD `2190fb0` detached, 35-file fingerprint all OK (`c2_fingerprint.txt`, SHA-256 `a124d35d…`); eval set `bd23fe48…`; lexicon `bcf0d184…`; C1 cache mappings unchanged.
- **M1 copy:** `C:\Users\sunny\r7-m1-measure`, a separate `git clone --local` at `2190fb0` (detached, `origin` removed), with the 35 C2 files copied and verified (**35 OK**) and the C2 replay result copied. Same 144 Python packages. No `.env`/`.env.local`.
- **End state:** the 35 C2 files are still OK in the M1 copy (the gate was not modified). C2 (35 OK), C1 (27 OK) and the Round-6 checkout (24 OK, no tracked change) are untouched. M1 adds only `experiments/round7_medication_role/` (15 files). Nothing staged, committed or pushed.

## 2. Criteria and sample (frozen before any gate run)

| Artifact | SHA-256 | Frozen |
|---|---|---|
| `CRITERIA_V1.md` | `68599b40…8034b` | 2026-10-28 00:04:48 +05:30 |
| `MEDROLE_SAMPLE_V1.jsonl` (191 rows, labels included) | `fc6c0570…24f31` | 00:09:25 |
| `review/BLIND_REVIEW_PACKET_V1.csv` (no labels, no gate output) | `9e0f26c8…8970` | 00:09:25 |
| Run started | — | after 00:09:25; the runner refuses to start if either hash differs |

The criteria define a drug role **linguistically**, including wordings C2 does not recognise, so a gate miss is counted as a miss. One caveat recorded honestly: some constructed texts had already been used in C2's own development tests; those rows carry `seen_in_c2_development: true` (23 rows).

**Rows by category and origin**

| Category | Real model | Constructed | Minimum | Met |
|---|---|---|---|---|
| Ordinary medication claims | 2 | 18 | 20 | yes |
| Compound claims | 0 | 10 | 10 | yes (all constructed) |
| Drug-class statements | 4 | 10 | 10 | yes |
| Contextual medication mentions | 4 | 10 | 10 | yes |
| Common-word collisions | 0 | 8 | 8 | yes |
| Unfamiliar proper nouns | 0 | 8 | 8 | yes |
| Valid non-medical statements | 0 | 10 | 10 | yes |
| Unsupported / wrong-identity | 0 | 25 | 15 | yes |
| Interaction claims (extra) | 37 | 0 | — | — |
| Uncited other statements (extra) | 45 | 0 | — | — |
| **Total** | **92** | **99** | 91 | |

**Real rows:** all 92 come from the recorded live runs of 14–18 Oct (`reports/live_validation/runs/…`; Groq, Cloudflare, NVIDIA, or "auto" where the artifact did not record the provider). They are split exactly as the live pipeline splits a conclusion. All of them concern simvastatin/clarithromycin and cite the synthetic simvastatin corpus chunk. That chunk has no verified source identity, so these rows are **gate-only**; their final release could not be evaluated. 72 of them cite nothing (an older prompt), and are reported as a separate uncited stratum; 20 cite the chunk. No real model output exists for compound claims, common words, proper nouns or the negative set, so those are constructed. **No new real-model generation was run:** the isolated copy deliberately has no credentials.

**Labelling:** AI-preliminary for all 191 rows (`label_origin: ai_preliminary`). The blind packet has the statement, the confirmed medications and the cited passages, with empty columns for the owner's decision, failing clause and rationale. When the owner fills it in, `m1_metrics.py` uses the owner's label wherever present (tested).

## 3. Execution, by kind

| Kind | What ran |
|---|---|
| Deterministic | 8 schema and metric tests (`test_m1_metrics.py`): 8 passed. Gate-only evaluation of the 92 real rows with the unmodified `identity_gate`. |
| Full release path, real NLI, **scripted generation** | 99 constructed rows through `LiveMedicalRAGService.execute` with the pinned `pritamdeka/PubMedBERT-MNLI-MedNLI@f1b6ce2e…` loaded offline, and lisinopril 5.5/7.1 and warfarin 7.3 approved in a temporary folder only (the round-5 harness). The row's text is the scripted answer. |
| Real-model generation | none new (section 2) |
| Browser / UI | **not run** |

## 4. Metric A: identity false withholding (expected PASS, gate REJECT)

Denominator: cited rows labelled PASS. Uncited rows are reported separately.

| Category | False withholds / valid | Rate |
|---|---|---|
| **Overall (cited)** | **1 / 87** | **1.1%** |
| Ordinary | 0 / 20 | 0% |
| Interaction (real) | 0 / 15 | 0% |
| Drug class | 0 / 12 | 0% |
| Contextual | 0 / 10 | 0% |
| Common word | 0 / 8 | 0% |
| Proper noun | **1 / 8** | 12.5% |
| Non-medical | 0 / 10 | 0% |
| Compound (valid) | 0 / 4 | 0% |
| Uncited stratum | 0 / 36 | 0% |

**The one false withhold, C-PN-06:** "The FDA label for warfarin lists drugs that increase bleeding risk [Source 1]." The effect-subject pattern took "The FDA label for warfarin lists drugs that" as the subject, cut it to "FDA label", which 7.3 does not name, and rejected it as `UNRESOLVED`. **Cause:** a non-subject verb ("lists") before a relative clause ("drugs that increase") is read as part of the subject. This is a gate defect for a later candidate.

With 87 valid rows, a 0% category rate does not show the true rate is zero.

## 5. Metric B: residual unsupported medication claims

68 rows labelled REJECT: 32 run through the full path, and 36 uncited real rows that are gate-only.

| Pattern | Tested | Gate rejected | Gate missed | **Released as verified** |
|---|---|---|---|---|
| Effect subject (P06–P09, P01, uncited invented) | 7 | 7 | 0 | 0 |
| Agent ("X-induced") | 1 | 1 | 0 | 0 |
| Structured fields (adverse reaction, interaction) | 2 | 2 | 0 | 0 |
| Ambiguous name (camphor) | 1 | 1 | 0 | 0 |
| Class named in other words ("NSAIDs") | 1 | 1 | 0 | 0 |
| Compound, later clause in a recognised role | 4 | 4 | 0 | 0 |
| **Effect before the drug** | 5 | 1 | 4 | **3**: C-NEG-07 "Metamizole is associated with hyperkalemia", C-NEG-08 "Hyperkalemia is a known risk with metamizole", C-NEG-09 "With metamizole, potassium levels can rise" |
| **Implicit / anaphoric subject** | 2 | 0 | 2 | **2**: C-NEG-13 "It can cause hyperkalemia …", C-NEG-14 "This drug can cause hyperkalemia …" |
| **Nested** | 3 | 2 | 1 | **1**: C-NEG-15 "Patients whose regimen includes Zorbitrex alongside lisinopril can develop hyperkalemia" |
| Passive outside the list | 3 | 1 | 2 | 0, but **only because the NLI did not entail** C-NEG-10 ("reported with Zorbitrex") and C-NEG-11 ("triggered by Zorbitrex") |
| Compound, later clause effect-first | 2 | 0 | 2 | 0, again only because the NLI did not entail (C-CMP-06, C-CMP-10) |
| Uncited real rows (gate-only) | 36 | 18 | 18 | not evaluable; these all lack a citation, which the release path withholds anyway |

Further details:
- **C-NEG-17** ("Hyperkalemia is a known risk with furosemide") was missed by the gate and withheld by the **round-6 guard**, because furosemide is in the lexicon. The same wording with metamizole (C-NEG-08) was released.
- **All 6 releases cite lisinopril §7.1 retrieved alone, or §5.5 + 7.1, as in the original defects.**
- **The 18 uncited gate misses** are instructions such as "Clinicians should avoid co-prescribing these medications…" and uncited "Concomitant use of X with Y is contraindicated." C2 has no role pattern for "avoid … these medications" or "Concomitant use of X with Y is contraindicated" (no "with" after "contraindicated").
- **Scope:** 0 releases in any one pattern on this small sample does not show the pattern is safe.

## 6. Metric C: valid non-medication handling

The C2 gate withheld none of the valid proper-noun, common-word, non-medical, contextual or class rows, except C-PN-06 (section 4). Other withholds among those valid rows came from **existing** checks, not C2:
- **Round-6 medication guard:** C-CWD-03 "Perform …" and C-CWD-04 "Align …". These are RxNorm brands written in capitals and not named by the source. This is the approved round-6 fail-safe.
- **The real NLI did not entail the cited section:** C-CWD-01, 05, 06, 07; C-PN-02, 05, 08; C-CTX-04. Several of these rows are only loosely supported by their section by design (the criteria score identity, not support).
- **Pair identity UNAVAILABLE plus the verifier aggregate:** C-CTX-08, C-CLS-09, C-PN-07. These name two requested medications, and the warfarin–ibuprofen candidate is not approved in the harness, so it gives no relationship identity.

## 7. Metric D: compound claims

| Row | Expected | Gate | Failing clause surfaced | Released |
|---|---|---|---|---|
| C-CMP-01, 02, 04 | PASS | PASS | — | yes |
| C-CMP-03 | PASS | PASS | — | no (pair identity UNAVAILABLE, verifier aggregate) |
| C-CMP-05, 07, 08, 09 | REJECT (clause 2) | REJECT | **yes, clause 2** | no |
| C-CMP-06 "…, and metamizole is associated with hypotension" | REJECT (clause 2) | **PASS** | **no** | no (the NLI did not entail) |
| C-CMP-10 "…, and the effect is larger with Zorbitrex" | REJECT (clause 2) | **PASS** | **no** | no (the NLI did not entail) |

A valid first clause never hid a later clause that C2 *recognises*. When the later clause uses an unrecognised wording, the gate passes the whole claim. Only the NLI stopped those two rows here.

## 8. Metric E: final answer behaviour (99 full-path rows)

| Identity gate | Released | Withheld |
|---|---|---|
| PASS | 49 | 28 |
| REJECT | 0 | 22 |

- **Gate PASS but withheld** (28): mostly the verifier, through non-entailment or the aggregate, or pair identity UNAVAILABLE. Also the round-6 guard (3 rows). These are evidence-support or other-check decisions, not identity errors.
- **Gate REJECT where every other check passed** (the gate alone withheld it), 8 rows:
  - P07-single and P08-single (C-NEG-03, 04);
  - C-NEG-16, 21, 22, 23;
  - C-CLS-07 ("NSAIDs", correct under the criteria);
  - C-PN-06 (the false withhold).

## 9. Frozen 42-example set

Rerun in the M1 copy with the real model. The result file is **byte-identical** to the C2 replay (SHA-256 `6b7bc451…`): 9 released, 0 false releases, the same 5 false withholds (D02, E06, E07, E09, E10), identity-gate rejections only on D05, E08 and E27 (already withheld), and no outcome change.

## 10. Findings needing new implementation work (a later candidate, not M1)

1. **Effect-before-drug wordings** (BLOCKING; 3 releases): "X is associated with Y", "Y is a known risk with X", "With X, Y …", "the effect is larger with X". These need patterns for "associated with X", "risk with X", "with X" as a fronted or trailing adjunct, and "reported with X".
2. **Implicit and anaphoric subjects** (BLOCKING; 2 releases): an anaphor with no grounded referent earlier in the same answer passes today. This needs answer-level referent tracking, or treating an unanchored "it / this drug" in a drug role as unresolved.
3. **Nested exposure phrases** (BLOCKING; 1 release): "whose regimen includes X", "X alongside Y", "combined with X".
4. **Passives outside the list** (gate miss; withheld only by the NLI): "triggered by", "reported with", "seen with".
5. **Administration instructions and "Concomitant use of X with Y is contraindicated"** (gate miss; uncited in this sample).
6. **False withhold** from a verb before a relative clause ("lists drugs that increase"): subject extraction should stop at a finite verb.
7. **The criteria leave one case open:** an anaphor inside an uncited claim. Rows R-040 and R-065 were labelled REJECT under rule 2.3; the owner should confirm that reading.

## 11. Remaining blockers and next step

- **Medication-identity coverage stays BLOCKED.** Unsupported medication claims are still released in 3 wording families (items 1–3).
- **The labels are not reviewed.** The owner's blind review of `review/BLIND_REVIEW_PACKET_V1.csv` (191 rows) is needed before these rates can be called reviewed. Until then they are AI-preliminary.
- **Recommended next step:** a remediation candidate (C2b) for items 1–6, built from C2 in its own isolated copy. It should include these M1 rows as regression tests, then rerun M1 on a fresh sample with the owner's labels. C3 stays paused until then.

## Artifacts (M1 copy, `experiments/round7_medication_role/`)

| File | Contents |
|---|---|
| `CRITERIA_V1.md` | the frozen criteria |
| `MEDROLE_SAMPLE_V1.jsonl` and `MEDROLE_SAMPLE_V1_MANIFEST.json` | the frozen sample and manifest |
| `review/BLIND_REVIEW_PACKET_V1.csv` | the owner's blind review packet |
| `build_sample.py`, `freeze_sample.py`, `run_m1.py`, `m1_metrics.py`, `test_m1_metrics.py` | scripts and tests |
| `inputs/` | the extracted real rows and their extraction scripts |
| `results/M1_RESULTS_V1.jsonl` (`0c9fa949…`) | per-row results |
| `results/M1_METRICS_V1.json` (`9ac0f067…`) | metrics |
| `results/FROZEN_SET_REPLAY_M1.json` | the frozen-set rerun |

Logs are in `C:\Users\sunny\r7-m1-logs\`.

Stopped after M1. The C2 gate was not modified, and C3 has not started.
