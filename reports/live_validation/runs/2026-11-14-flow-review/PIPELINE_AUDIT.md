# Backend pipeline audit: 2026-11-14

- **Code:** `wip/pre-threads-20261022-1440` at `c5d4100`.
- **Where:** the live app at http://localhost:5173, which forwards to 127.0.0.1:8000.
- **Inputs:** synthetic only.

## Question: why does every analysis abstain?

**This is not a code bug.** The live app has no evidence with a verified source identity. The gate that rejects it is working as designed.

### Evidence

1. **The live corpus.** The app loads `data/live_medical/LIVE_MEDICAL_CORPUS_V2.json`, 14 chunks (`live_application.py:1655`, `:1766`).
   - None of the 14 chunks carries a `source_identity` record.
   - Every DailyMed chunk has a placeholder URL, for example `...drugInfo.cfm?setid=example-warfarin`.
   - `PMID 31234567` is attached to two different documents: `PMID-31234567` and `PUBMED-31234567-001`.
2. **The gate** (`live_application.py:1031–1046`, `live_source_links.py`):
   - A chunk is used only if `source_link()` returns VERIFIED.
   - VERIFIED requires the chunk to be in `verified_source_links`.
   - `verified_source_links` is built only from evidence in *approved* V2 relationship datasets (`live_application.py:1806–1812`).
   - The frozen corpus can never become verified by itself. This is deliberate and documented in the `live_source_links.py` module docstring and `tests/e2e/test_live_evidence_provenance.py:119`.
3. **No approved dataset exists.**
   - `data/live_medical/relationships/` holds only the V1 manifest, with status `CANDIDATE_PENDING_RESEARCHER_APPROVAL` and no approval. There is no V2 dataset and no `v2/` folder.
   - Every V2 manifest on this machine is `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, with no `approved_by`:
     - `reports/live_validation/runs/2026-10-15T0448Z-acf08ee-revalidation/relationship_v2_candidate_r2/`
     - `reports/live_validation/runs/2026-10-22-audit/{rel_live_0003,rel_live_0004,food_0001}_candidate/`
     - the matching copies in `tests/fixtures/`
     - the `c2j-work` and `cwt-feat` worktrees, which have V1 only, also pending.
   - No V2 dataset has ever been committed on any branch.
4. **Why the 15 Oct run differed.** That run scored `SPL-SIMVASTATIN-001` at 0.94. The hard source-identity gate came later, in `a96e171` on 2026-10-22. After that, placeholder-URL chunks can no longer be scored.
5. **The paper's verified DailyMed sections.** These are the candidate V2 datasets above. The tests and the evaluation workspace load them from an approved *temporary copy*. The live app's data folder has never had an approved copy.

### Live runs: the gate's decision on each chunk

| Pair | RxNorm | Chunks naming the drugs | Rejected chunks (link status) | Outcome |
|---|---|---|---|---|
| simvastatin + clarithromycin | 36567, 21212 (MATCHED) | 1 | SIMVASTATIN-001 (PLACEHOLDER) | Abstain, R2, trust not computed |
| lisinopril + metformin | 29046, 6809 (MATCHED) | 4 | LISINOPRIL-001/002, METFORMIN-001 (PLACEHOLDER); PMID-31234567 (SHARED) | Abstain, R2 |
| warfarin + ibuprofen | 11289, 5640 (MATCHED) | 2 | WARFARIN-001, IBUPROFEN-001 (PLACEHOLDER) | Abstain, R2 |

## Stage by stage

| Stage | Observed | As intended? |
|---|---|---|
| Input screening and sanitisation | An injection note was rejected with `INPUT_REJECTED`, and the markers were logged. Clean notes passed. | Yes |
| Image / vision | Groq vision `qwen/qwen3.8-27b` returned 2 candidates (HIGH confidence) in 1.9 s. Raw label text is not resolved without user confirmation. | Yes |
| RxNorm normalisation | All six drugs matched by curated mapping. An approximate match (similarity 0.70) was refused. | Yes |
| Retrieval | Hybrid retrieval over 14 chunks with `all-MiniLM-L6-v2` (real embeddings). `top_k` = 20 is larger than the corpus, so every chunk comes back each time. | Yes. Ranking has no effect on this corpus size. |
| Evidence admission | Provenance and hash checks, injection and poisoning checks: ALLOW. Alignment: unrelated chunks excluded (10–13 per pair). Source identity: every relevant chunk REJECTED (see above). | Yes |
| Trust scoring and risk tier | R2 for drug pairs, R0 for single drugs. Thresholds 0.60 and 0.30, unchanged. Score `NO_ELIGIBLE_EVIDENCE` (not a computed zero). | Yes |
| LLM routing, claim verification, identity gate, release | Not reached live: nothing passes admission. The positive path is covered by `tests/e2e/test_live_evidence_provenance.py`, `test_citation_alignment.py` and `test_live_failure_semantics.py`, which approve a candidate in a temporary folder: **114 passed, 1 xfail** today. | Yes, in tests |
| Abstention and SSE | Structured abstention gives the reason and lists every excluded chunk with its link and identity status. Food guidance is `NOT_RUN`. The stream closes without `complete`, which the UI handles. | Yes |

## Fixes

No backend bug found, so no backend change.

The UI fixes from this session are listed in `FLOW_REVIEW.md` (`886b0b0` … `88346f6`). The full checks ran after those fixes:
- backend 1899 passed, 0 failed;
- frontend 150 of 150 tests, build passes, 0 lint warnings;
- ruff and bandit clean.

Nothing has changed in the code since then.

## Needs Sandeep's decision (not changed)

To let the live app answer, a researcher must review and approve a V2 dataset. For example, `relationship_v2_candidate_r2`, or `rel_live_0003` / `rel_live_0004` / `food_0001`. Approving means:
- setting `status: APPROVED`, with `approved_by` and `approved_at`;
- keeping the file hashes matching;
- placing the dataset in `data/live_medical/relationships/` or under `relationships/v2/<name>/`.

Its evidence then joins retrieval with a verified identity, and only the pairs it covers can be answered. Every other pair will still abstain.

This is a research and evidence decision, so I did not make it. I did not edit the corpus, the relationship records or the thresholds.
