# Addendum: decision B, REL-LIVE-0002 review, V2 evidence path, hook and Bandit

This continues `ACF08EE_REVALIDATION_REPORT.md` in the same run folder.
- **2026-10-15, 05:19–05:40 UTC:** the work itself was done.
- **2026-10-17:** the state was rechecked after the PC came back online. The four changed files are byte-identical to the ones the full suite ran against, and a rerun of the three live-pipeline test files passed 130 of 130.

Nothing was pushed, tagged, reset, cleaned or stashed. No commit was made beyond the two Sandeep asked for. REL-LIVE-0001 and REL-LIVE-0002 are both unapproved, and `approved_by` / `approved_at` were never filled in. Sandeep's uncommitted and untracked work is untouched.

## 1. Local commits (decision B, not pushed)

| Commit | Content | Built from |
|---|---|---|
| `2947976e0f2b71e6b7fd48ebe3a8fb5dc04f8401` | fix(live): link only verified evidence sources; stop Cloudflare answers being cut off (11 files) | `git apply --cached` of patch 0001 |
| `b5474cea2ff561ecc1df2326769ef67bb6339431` | feat(live): name the provider and model that served every outcome (3 files) | `git apply --cached` of patch 0002 |

How they were built and checked:
- Each commit was staged into the index only, with no `git add`, stash or reset. Before each commit, every changed line in the staged diff equalled the patch.
- The repo's pre-commit secret gate (`.githooks`: regex scan plus `gitleaks git --staged`) passed both commits.
- All 12 files in HEAD equal their EXPECTED_BLOBS values. app.py carries only the max-tokens change, and Sandeep's NVIDIA lines stay uncommitted.
- `origin/ui/3d-redesign` and `git ls-remote` both still point to `c490393`, and no tag exists. Evidence: `commits/verify_after_commits.txt`.

## 2. REL-LIVE-0002 formal review (still CANDIDATE_PENDING_RESEARCHER_APPROVAL)

- **Checks:** `source_review/review_v2_candidate.py` is separate from the builder, and reads the XML with ElementTree rather than regex. **34 of 34 checks pass** (`source_review/review_v2_candidate_output.txt`):
  - the manifest is pending with a null approval, and its records hash matches the records file;
  - all 6 capture files match the sizes and sha256 values in CAPTURE_MANIFEST;
  - setId `9aaffb41-408c-4372-8fd5-1d649450c0e9`, version 21, effectiveTime 20231010;
  - the URL is `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9aaffb41-…`;
  - bytes 75723–76181 are a single `<paragraph>` with raw sha256 `1bc9541f…e874`;
  - the section "4.5 Lomitapide, Lovastatin, and Simvastatin" paragraph, extracted by the XML parser, equals the chunk text and the record's `evidence_span`;
  - content hash `056d8009…`;
  - the span names both drugs and says the combination "is contraindicated";
  - RxNav 36567 is simvastatin and 21212 is clarithromycin, both TTY IN and not suppressed;
  - CONTRAINDICATION / CONTRAINDICATED / BIDIRECTIONAL;
  - the all-MiniLM-L6-v2 embedding reproduces with cosine 1.000000;
  - the chunk id is new, and there is no candidate file under `data/`.
- **Scope of the record:** the contraindication of taking the two together only. The span names simvastatin as one of the "HMG-CoA reductase inhibitors … extensively metabolized by CYP3A4". Mechanisms and adverse effects beyond the span are not verified by this record.
- **The source label:** Aurobindo's generic clarithromycin SPL, not the innovator label.
- **Revision 2 (`relationship_v2_candidate_r2/`):** the same record, text, hash and embedding, in the layout the V2 loader reads.
  - It adds `authority` 0.95, `freshness` 0.9 (the values the frozen corpus gives DailyMed chunks) and `provenance.content_hash`.
  - Records sha256 `541f5d35…`, evidence sha256 `f84f304e…`.
  - Status pending, approval null.
  - Revision 1 (`relationship_v2_candidate/`) is kept.

## 3. V2 evidence-loading path (uncommitted; full diff in `v2_loader_and_hook_fix.diff`)

**What changed**
- `services/live_relationships.py` reads `LIVE_RELATIONSHIP_RECORDS_V2` next to V1. If there is no V2 manifest, the store is exactly the V1 store.
- V2 loads only when all of these hold:
  - the status is APPROVED, with `approved_by` and `approved_at`;
  - `records_sha256` and `evidence_sha256` both match (LF-normalised).
- Each evidence chunk must:
  - be complete;
  - have `content_hash` = sha256(text), with `provenance.content_hash` equal to it and a named provenance source;
  - have an https URL;
  - have authority and freshness in [0, 1];
  - have an embedding of the corpus's dimension;
  - not reuse a frozen chunk id.
- Records are checked with the unchanged `validate_record`, against the frozen corpus plus the accepted V2 chunks.
  - Only chunks that an accepted record cites become retrievable.
  - V1 records can still cite only the frozen corpus.
- `_lazy_init_models` adds those chunks to retrieval and to the embedding lookup. `retrieval_info` and the `retrieval` event list them under `relationship_evidence_chunks`, which appears only when some are loaded.
- The retrieval-time hash check, trust scoring, eligibility, unrelated-evidence exclusion and ClaimVerifierV2 all apply unchanged.
- `canonical_identity.py`, `claim_verifier_v2.py`, the thresholds, the R2/R3 rule and the frozen corpus are untouched.

**Tests:** `tests/e2e/test_live_relationship_evidence_v2.py` has 35 tests. The fixtures are synthetic and written to a temporary folder; the real candidate is never used.
- Positive:
  - an approved dataset loads its record and chunk and gives R3;
  - the contraindication claim is SUPPORTED / MATCH in either drug order;
  - the chunk joins retrieval through `_lazy_init_models`.
- Fail-closed:
  - a pending manifest, or a manifest without a named approval;
  - a records or evidence hash mismatch;
  - edited text with a recomputed manifest;
  - a bad content or provenance hash, or a missing provenance source;
  - http instead of https, a wrong embedding dimension, a missing field;
  - a chunk id that collides with the frozen corpus, or a chunk no record cites;
  - a wrong drug pair, an invalid predicate, a directional predicate marked bidirectional, an unknown or invalid direction, a span that is not verbatim;
  - a claim with the wrong predicate, a query for another pair;
  - a V1 record citing V2 evidence;
  - text altered at retrieval time;
  - unrelated evidence still excluded.

**Dry run with real models** (`source_review/dryrun_v2_candidate_output.txt`)
- Real all-MiniLM-L6-v2 retrieval over the frozen corpus and the real ClaimVerifierV2 NLI model. The normalizer is a stub, and the LLM returns a fixed one-sentence answer.
- The "approved" copies were temporary folders outside the repository, labelled DRY-RUN and deleted afterwards.

| Case | Retrieved | Tier | Claim result | Outcome |
|---|---|---|---|---|
| Pending r2, as it is | 14, no V2 chunk | R2 / 0.60 | UNSUPPORTED / UNAVAILABLE | abstention |
| DRY-RUN approved copy | 15, V2 label chunk included | R3 / 0.75, basis REL-LIVE-0002 | "Simvastatin with clarithromycin is contraindicated": SUPPORTED / MATCH | **answer** |
| Same, reversed drug order | 15 | R3 | SUPPORTED / MATCH | answer |
| Same, "Simvastatin inhibits clarithromycin" | 15 | R3 | UNSUPPORTED / MISMATCH | abstention |
| Same, "… causes liver failure" | 15 | R3 | UNSUPPORTED (entailment 0.001) | abstention |
| Approved copy with edited evidence bytes | 14 (evidence hash mismatch) | R2 | UNSUPPORTED / UNAVAILABLE | abstention |

- **In the approved case:** the frozen placeholder chunk `DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01` is also eligible and shown, still marked "Not linked". The relationship identity comes only from the V2 label chunk.
- **The shipped app:** unchanged until a V2 dataset is placed in `data/live_medical/relationships/`, and none is.
- **The backend on :8000:** it was started before this change, so it ran without the V2 path. It is no longer running after the PC went offline.

## 4. Secret-scan hook and Bandit

**Hook** (`.agents/scripts/ci/pre_commit_secret_scan.py`, uncommitted)
- `--quiet` is replaced by `--no-banner --log-level error --redact --exit-code 1`.
- Exit 1 means a secret was found. Any other non-zero exit now reports "could not run" instead of pretending a secret was found. Both still block.
- Results (`checks/secret_scan_hook_after_fix.txt`):
  - A random fake GitHub-token-shaped string, generated in memory and never written to disk, is denied by both the gitleaks layer and the regex layer.
  - Clean code and env-var references are allowed.
  - The repo's `check_secret_scan_allow.py` and `check_secret_scan_deny.py` pass locally (gitleaks active) and with CI=1.
  - All 15 changed files are allowed.
  - The saved output contains no token text.
- `.githooks/pre_commit_secret_scan.py` (the commit gate) and the copy in `.agents/scripts/` (the Claude write hook) never passed `--quiet`, and were not changed.

**Bandit B110** at `src/adaptive_trust_medical_rag/annotation/engine.py:220` (Sandeep's untracked file, not edited)
- **What the code does:** in `_initialize_backend`, the fallback that builds a HuggingFace or FreeLLMAPI `LLMProviderAdapter` is wrapped in `except Exception: pass`, and the method returns None. `annotate_position` then raises "LLM backend … is not configured or missing credentials". So it fails closed, but an import or constructor error is hidden behind a misleading message.
- **Options:**
  - (a) log the exception type and message, then return None (keeps the behaviour, clears B110);
  - (b) catch only `ImportError`, so other errors surface;
  - (c) add `# nosec B110` with a reason;
  - (d) keep `annotation/` out of the freeze.
- `run_bandit.py` still exits 1 until one of these is chosen.

## 5. Checks after this work

| Check | Result |
|---|---|
| Focused pytest (12 files incl. the V2 tests), working copy, TESTING=1 | **278 passed, 0 failed** (`checks/pytest_focused2.txt`). The first attempt failed 1 existing test because `retrieval_info` always carried the new key; fixed by adding the key only when V2 evidence loads (`checks/pytest_focused2_attempt1_retrieval_info_key.txt`). `git status` unchanged by the run |
| Full suite in temporary worktree `C:\Users\sunny\acf08ee-fullsuite-wt2` (detached `b5474ce` plus a copy of the current working-copy code; blobs checked) | **1403 passed, 4 skipped** (`checks/pytest_full_worktree2.txt`). The earlier run, whose files changed mid-run, is kept as `…_attempt1_superseded.txt` |
| Recheck 2026-10-17: V2, risk-eligibility and failure-semantics tests | 130 passed |
| vitest | 15 files, 93 passed |
| ruff | clean |
| verify_v3_1_integrity / verify_v3_confirmed_separation | PASS / PASS |
| Bandit on the changed source files | exit 0 |
| run_bandit.py | exit 1 (only B110 in the untracked annotation file) |
| Protected hashes vs 2026-10-14 | 19 OK; app.py differs as expected (max-tokens) |
| `data/` | unchanged |

## 6. Freeze decision

| Field | Value |
|---|---|
| CONFIRMATION_CONTRACT_FIXED | YES |
| REAL_EMBEDDING_RETRIEVAL_VERIFIED | YES |
| CONTROLLED_ABSTENTION_VERIFIED | YES |
| CLOUDFLARE_OUTPUT_VALIDATED | YES (one synthetic run) |
| EVIDENCE_SOURCE_LINKS_VALIDATED | YES |
| PROVIDER_MODEL_TRACE_VERIFIED | YES for abstention and error (live); answer path in tests and the dry run |
| RELATIONSHIP_RECORD_VERIFIED_PENDING_APPROVAL | YES: REL-LIVE-0002 r2 passed 34/34 checks, and a runtime path can load it once approved |
| RELATIONSHIP_RECORD_APPROVED | NO |
| EVIDENCE_BACKED_ANSWER_VERIFIED | NO (dry run with a temporary copy only; no researcher approval, no app run) |
| APPLICATION_FREEZE_READY | **NO** |

What still blocks the safe-abstention-only freeze:
1. No single commit equals the tested build. Sandeep's NVIDIA LLM/OCR edits, the hook fix and the V2 path are uncommitted.
2. `run_bandit.py` exits 1 (B110: Sandeep picks option a, b, c or d).
3. BLK-011: the full suite still rewrites 7 tracked evidence files on `ui/3d-redesign`.
4. B-LIVE-DISCLAIMER-RESIDUE and B-LIVE-NVIDIA-LLM-TIMEOUT are still open. Neither releases unsafe content.

What Sandeep needs to decide:
- whether to commit the hook fix and the V2 path, and his NVIDIA edits;
- the B110 option;
- BLK-011;
- approve, amend or reject REL-LIVE-0002 r2, and whether to place it in `data/live_medical/relationships/` afterwards;
- removing the two temporary worktrees: `git worktree remove C:\Users\sunny\acf08ee-fullsuite-wt` and `git worktree remove C:\Users\sunny\acf08ee-fullsuite-wt2`.
