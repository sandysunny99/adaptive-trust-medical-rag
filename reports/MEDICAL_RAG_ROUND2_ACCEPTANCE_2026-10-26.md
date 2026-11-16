# Medical RAG round-2 acceptance report (2026-10-26)

Research prototype. Nothing here is clinical advice. No software result in this report grades or approves clinical evidence.

This report follows `reports/MEDICAL_RAG_FULL_SYSTEM_AUDIT_2026-10-26.md` (round 1, ended at `0c17e7c`).
Branch `wip/pre-threads-20261022-1440`. Round 2 covers `0c17e7c..5c42bbc`: 11 local commits, nothing pushed.

Evidence labels: **[unit]** unit test · **[int]** service-level integration with stubs · **[mock-provider]** scripted LLM or vision provider · **[real-provider]** real Groq, Cloudflare, NVIDIA or RxNav · **[http]** real HTTP/SSE against the running app · **[browser]** the real UI in a browser · **[source]** code reading only. Nothing here comes from clinical review.

---

## A. Executive summary

**Engineering acceptance: PASS, with the limits listed in section E. Production or clinical readiness: not established.**

| Acceptance rule | Result |
|---|---|
| Negative path: unsupported, unverified or ineligible evidence gives an abstention or a withheld claim | **PASS** [http][browser] warfarin + ibuprofen abstains on placeholder sources, and no model is called. [real-provider] withheld answers name each failed statement. |
| Positive path: eligible evidence gives a traceable answer whose claims and citations pass verification, and the browser shows it correctly | **PASS** [browser][real-provider] lisinopril + spironolactone released with "Claim verification (9 of 9 verified)", two verified DailyMed links and trust 0.66 (R2). Across 12 real Groq runs (V2 prompt, corrected trust), the pair was released 4/6 times and lisinopril alone 2/6. Every withheld run named the statements that failed. |
| The positive path uses only test-approved evidence | **Yes.** Real DailyMed text (FOOD-0001 and REL-LIVE-0003 fixtures) was copied to a scratch folder outside the repository and approved there as "AUDIT TEST FIXTURE (not clinical)". `data/live_medical` is unchanged, so **the live application still abstains on every question** until a reviewer approves evidence. |

The positive path now works because of four fixes found by running the real model, not by unit tests. Three fixed the generation/verification contract: the V2 prompt, the "raised risk" parse, and per-sentence verification. The fourth corrected the trust score (`51fb6cc`).

---

## B. Findings and fixes (round 2)

| ID | Sev | Root cause | Regression test | Commit |
|---|---|---|---|---|
| R2-01 | **P1** | LIVE_APP_PROMPT_V1 asked for an uncited conclusion (with a disclaimer and a follow-up recommendation) and an uncited claims list. The verifier (since AUD-09) withholds uncited statements, so real answers could never be released. | `tests/e2e/test_live_prompt_versions.py` | `160570c` V2 prompt with a citation contract. V1 is byte-identical (`e4a63bd3…`) and selectable with `LIVE_APP_PROMPT_VERSION=V1`. Both are hash-checked at load; `.gitattributes` pins them to LF. |
| R2-02 | **P1** | A prompt that failed to load left `""`, which was still sent to the model, and the answer was released. Reproduced: one call with a 0-character prompt. | same file, 3 cases | `160570c` `PROMPT_UNAVAILABLE` before any model call |
| R2-03 | P2 | `extract_claim_identity` read "spironolactone can **increase** the risk of hyperkalemia when used with lisinopril" as drug-to-drug `INCREASES`, so it never matched the approved `INTERACTION` record. | `tests/test_canonical_identity.py` (6 phrasings; research callers unchanged) | `510e31b` live claims only |
| R2-04 | P2 | The whole conclusion was one statement, so a single-drug sentence was forced through the pair-identity check and withheld. | `test_each_conclusion_sentence_is_verified_on_its_own` | `0ab05d0` |
| R2-05 | **P1** (OPEN-1) | `query_relevance` was a constant 0.85 (it read a nonexistent attribute); `evidence_quality` copied authority; population and freshness defaulted to 0.8; `missing_factors` was always `[]`. | `test_unmeasured_factors_are_missing_not_defaulted`, `test_measured_relevance_is_the_vector_similarity`, RRF test | `51fb6cc` LIVE_TRUST_FACTORS_V2 (section C) |
| R2-06 | P2 | Groq vision returned 429 and extraction failed outright: a rate limit never moved to the configured NVIDIA fallback. | `test_a_rate_limit_moves_to_the_other_provider…` | `e0e1933` (a rate limit moves to another provider, not to another model of the same provider) |
| R2-07 | P2 | Vision required an NVIDIA key even when Groq's image model was configured. | `test_a_groq_key_alone_enables_vision` | `e0e1933` `build_vision_backend()`, `VISION_PRIMARY` |
| R2-08 | P2 (D3) | NVIDIA-first vision took about 62 s per upload (section D). | `test_groq_is_the_default_vision_primary` | `1ceeb6c` Groq-first by default |
| R2-09 | P2 (OPEN-6) | RxNav outages were swallowed and reported as an unresolved drug. | 3 tests (client, normalizer, stream) | `f2dd09b` `NORMALIZATION_SERVICE_UNAVAILABLE` |
| R2-10 | P2 | The medication card crashed on statuses `ERROR` (already sent by the backend) and `SERVICE_UNAVAILABLE`. | `MedicationCard.test.tsx` (3 tests failed before) | `f2dd09b` |
| R2-11 | P3 | A salt concept (warfarin sodium 114194) was shown without its RxNorm ingredient. | 2 tests, plus 1 for lookup robustness | `b52f308`, `5381e3d` (ingredient shown, **not substituted**; see E.3) |
| R2-12 | P2 | Food guidance showed one message for five different outcomes. | 5 backend and 4 vitest tests | `d5cedd4` `food_guidance_status` |
| R2-13 | P3 (OPEN-5) | The UI never listed per-claim results. | vitest | `d5cedd4` "Claim verification (N of M verified)" with the failure reason |

`5381e3d` fixed a regression introduced by `b52f308`: a client without an ingredient lookup aborted normalization. It was caught by the neighbouring suites before the full run. `5c42bbc` is an oxlint-only change.

Tests changed but not weakened. Fixture helpers that exercise later stages now state their assumptions: `FIXTURE_RELEVANCE = 0.6` (the real §7.1 chunk measured 0.57), and `FIXTURE_EVIDENCE_QUALITY = 0.95` in the two files that use R3 records. The c7 test runs with zero-stub test embeddings; it now asserts the abstention those embeddings produce. Two expected-reason strings were updated (`claim=INTERACTION`). One vision test dropped its 429 case, which is now covered by the new failover test.

---

## C. Trust score: before and after (formula, weights and thresholds unchanged)

Factor policy LIVE_TRUST_FACTORS_V2. Each factor is measured or missing, and a missing factor adds 0 (the scorer's existing full-denominator policy, also used by the research orchestrator for relevance, quality and population).

- `query_relevance` is the vector channel's cosine similarity, which `config/trust.yaml` defines it as. It is None if that channel did not return the chunk.
- `evidence_quality`, `population_match` and `freshness` come only from the evidence record.
- `consistency` = 1 − poisoning score (as in the research orchestrator; a proxy, not cross-source consensus).
- `entity_match` = 1 after the alignment gate. `anti_injection` = 1, because chunks that carry instructions are excluded.

| Chunk (DailyMed label, auth 0.95, fresh 0.90) | R0 (0.30) | R1 (0.45) | R2 (0.60) | R3 (0.75) |
|---|---|---|---|---|
| Before (0.85 relevance, quality = authority, population 0.8) | 0.9375 ✓ | 0.9325 ✓ | 0.9350 ✓ | 0.9415 ✓ |
| After, relevance not measured | 0.6325 ✓ | 0.5800 ✓ | 0.5775 ✗ | 0.5950 ✗ |
| After, measured relevance 0.57 (real §7.1, pair query) | about 0.75 ✓ | about 0.69 ✓ | **0.6634 ✓** [http] | about 0.65 ✗ |

The score is a heuristic for source confidence and ranking. It is not a probability of correctness. **No chunk can reach R3 until an evidence record carries a measured evidence quality**, so questions an approved severe record raises to R3 will always abstain. That is a research-protocol decision (E.2).

---

## D. Vision provider comparison [real-provider][http]

Same 10 synthetic prescriptions: clear, rotated, low-resolution, three drugs, similar names (hydroxyzine/hydralazine), brands (Coumadin/Advil), decimals (0.05 mg, 2.5 mg), cropped, missing strength, injected text.

| Order | Runs | Extracted | Drug names correct | Served by | Median / max total |
|---|---|---|---|---|---|
| NVIDIA-first (old default) | 10 | 10 | all | Groq 10 (NVIDIA timed out 2×30 s every time) | **62.2 s** / 64.5 s |
| Groq-first (new default), paced 10 s | 20 | 20 | all | Groq 13, NVIDIA 7 (after Groq 429) | **2.8 s** / 36.0 s (one Groq timeout, then a retry) |
| Groq-first, unpaced (before R2-06) | 20 planned | 3 | all of those 3 | Groq | 16 failed on Groq 429 with no failover; the last request hit the app's own 60/min rate limit |

Notes:
- Name accuracy is the same, because Groq served every NVIDIA-first run.
- Strength, form and frequency exist only inside the extracted raw text. The schema has no fields for them.
- On the injected image, Groq listed "CYANIDE 100 MG" as a HIGH-confidence candidate and NVIDIA did not. The mandatory confirmation step is the control.
- The comment on `DEFAULT_VISION_PRIMARY` and the `1ceeb6c` message say NVIDIA served 8; the measured count is 7.

---

## E. Remaining work, separated by owner

1. **Clinical or pharmacist review (required for any real answer):** no relationship or food evidence is approved in `data/live_medical`. REL-LIVE-0004 stays UNGRADED and unapproved.
2. **Research-protocol decisions:**
   - Evidence quality: measure it, for example from regulatory-label status, or accept that R3 always abstains.
   - Whether `consistency = 1 − poisoning` is acceptable.
   - Whether vector cosine is an adequate relevance signal (it is uncalibrated).
3. **Clinical rule:** whether a salt or brand concept (warfarin sodium, Coumadin) may use ingredient-level evidence. It is not substituted today (medical-safety.md).
4. **Engineering:**
   - Screen vision-transcribed text for injection, and show vision warnings in the UI.
   - The verifier rates some verbatim label sentences AMBIGUOUS ("attenuates potassium loss…"), which causes most of the remaining false withholdings.
   - There are no structured strength or frequency fields.
   - `/health` reports unhealthy without a database.
   - The app is built twice under `--factory`.
5. **Provider:** Cloudflare failover was exercised with mocks only (Groq never failed during real runs). Groq's vision rate limit is low.

---

## F. Validation and final state

All runs were on HEAD `5c42bbc` in sequence, with no code changes afterwards.

| Check | Command or evidence | Result |
|---|---|---|
| Backend, full | `TESTING=1 uv run pytest -q` | **1753 passed, exit 0** (round-1 end: 1719) |
| Backend, network blocked | same, with a dead HTTP(S) proxy and Hugging Face offline | **1753 passed, exit 0** |
| Fresh clone | `git clone` of the branch, `uv sync`, full suite | **1749 passed, 4 skipped, exit 0**; `git status` clean afterwards. The 4 skips are the provider-preflight tests, which skip without API keys. |
| Frontend | `vitest run`, `tsc -b`, `oxlint` | **139/139**, exit 0, exit 0 (3 pre-existing warnings) |
| Real HTTP/SSE [real-provider] | 12 lisinopril runs (6 pair, 6 single), warfarin + ibuprofen | pair released 4/6, single 2/6, warfarin + ibuprofen abstains |
| Browser [browser] | real UI, test-approved evidence server | positive: released, 9/9 claims verified, verified links; negative: abstention, food "not assessed", trust "not computed" |
| Vision [real-provider] | section D | Groq-first 20/20 |
| Mocked provider routing | `tests/providers`, routing tests | 70 passed |

- **Integrity:**
  - Frozen V1 corpus SHA-256 `1fdb0be6…78ca5578`, unchanged.
  - No change under `data/` or `config/`.
  - LIVE_APP_PROMPT_V1 is byte-identical (`e4a63bd3…`).
  - REL-LIVE-0004 is `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, approval `null`, severity `UNGRADED`, and not in `data/live_medical` (which holds only the V1 relationship files).
  - gitleaks over `054cf16..HEAD`: no leaks. `git diff --check`: clean.
- **`.env` / `.env.local`:** never opened. The permission rules deny reading them, and the effective configuration came from the app's startup log. No changes.
- **Nothing pushed.** Temporary dev-server configs were removed. The stale `experiments/runs/live-smoke-v1/*` files were left as found.
