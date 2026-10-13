# Focused Acceptance Test Review

Date: 2026-10-13

## Disposition

**Ready for review with real-provider extraction blocked by missing configuration.**

The UI error-message change and real prescription-image extraction were verified as separate concerns. The UI displays a disconnect-specific recovery message instead of claiming provider authentication failure. During browser acceptance, the native EventSource error event was also found to be entering the named SSE `error` handler with no `data`, which caused a secondary `JSON.parse(undefined)` console error. That defect was corrected and covered by frontend regression tests. A real vision-provider request could not be attempted because no supported provider credential is configured in the environment.

## Acceptance matrix

| Area | Status | Evidence |
|---|---|---|
| Visible navigation and primary controls | Verified | Local browser at `http://127.0.0.1:5174`; Overview, Medical RAG, History, Evidence, Security, Evaluation, Research Audit, upload mode, drug mode, Add drug, Analyze, Save/export actions are present and wired |
| Manual request failure messaging | Verified | Synthetic Warfarin request reached the live local API and the UI displayed `Analysis stream disconnected before completion. The request may not have finished; retry if needed.` rather than the old authentication claim |
| Native SSE error-event handling | Verified | Browser log reproduced `JSON.parse(undefined)` before the fix; `connectStream` now ignores error events without data, and `frontend/src/services/api.test.ts` covers native transport errors and terminal SSE errors |
| History persistence after refresh | Verified | Synthetic result seeded into IndexedDB, listed in History, browser reloaded, record remained listed |
| Reopen without rerun | Verified | Open saved record rendered the saved medication, conclusion, and evidence directly; no new model request was issued |
| Individual delete | Verified | Delete action removed the saved record and rendered `No saved analyses yet.` |
| Clear All confirmation | Verified | Cancelled confirmation preserved the record; accepted confirmation removed it |
| Markdown export | Verified | Browser download was intercepted; generated report contained synthetic conclusion/evidence and no context/instruction markers |
| JSON export | Verified | Browser download was intercepted; evidence was present while `SYNTHETIC_PATIENT_MARKER` and `SYNTHETIC_INSTRUCTION_MARKER` were absent |
| Evidence/Security empty and populated surfaces | Partially verified | Empty navigation and populated saved-result rendering were inspected; all partial pipeline visual states remain untested |
| Real prescription-image extraction | Blocked | `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CLOUDFLARE_API_TOKEN`, and `OPENAI_API_KEY` were all unset; no live request was issued |
| Deterministic image extraction and confirmation | Verified | `tests/api/test_prescription_vision_e2e.py` plus `tests/e2e/test_v6_c6_image_confirmation_rxnorm.py`: 6 passed |

## Exact tests

- `$env:TESTING='1'; uv run pytest -q`: 1,210 passed, 4 skipped, 513 warnings.
- `$env:TESTING='1'; uv run pytest -q tests/providers/test_vision_backend.py tests/test_model_selector.py`: 27 passed.
- `$env:TESTING='1'; uv run pytest -q tests/api/test_prescription_vision_e2e.py tests/e2e/test_v6_c6_image_confirmation_rxnorm.py`: 6 passed.
- `Set-Location frontend; npm run test -- --run`: 3 files, 17 tests passed.
- `Set-Location frontend; npm run test -- --run` after SSE regression fix: 4 files, 19 tests passed.
- `Set-Location frontend; npx --no-install tsc --noEmit`: passed.
- `Set-Location frontend; npm run build`: passed.
- `uv run ruff check src/ tests/`: passed.
- `uv run bandit -r src --ini .bandit -q`: passed.
- Gitleaks scan: no leaks found.
- `git diff --check`: passed.

## Image workflow conclusion

The deterministic tests establish that upload, candidate extraction through a mocked vision path, explicit confirmation, RxNorm progression, ambiguity blocking, malicious image-text handling, and direct-drug regression behave as intended. They do not establish that a real NVIDIA or other provider can extract a medication in this environment.

When a credentialed provider is available, the next acceptance action is to upload a synthetic prescription image, inspect the returned candidate list, explicitly confirm it, and verify the subsequent normalization and pipeline stages. No confirmation bypass or raw prescription/provider secret exposure was observed in the deterministic tests.

## Remaining corrective work

1. Configure an authorized vision provider in a controlled environment and run one synthetic-image acceptance request.
2. Add browser automation for upload, confirmation, partial-stage failures, and actual file downloads.
3. Keep the current disconnect-specific error; add stage-aware terminal error data so provider/schema/normalization failures are distinguished in the UI.

## Addendum: 2026-10-13 prescription stream follow-up

### Disposition

**Partially resolved and correctly diagnosed; live provider extraction remains blocked by configuration.**

The original image-analysis failure was not solely a provider failure. The current source contained two application-level stream defects:

1. The backend emitted `medication_candidates_extracted`, but `frontend/src/services/api.ts` did not register that event type. Candidate data therefore could not reach `useAnalysis`, preventing the confirmation UI from receiving the extracted medications.
2. If confirmation was not received before the backend timeout, `LiveMedicalRAGService.execute` returned without a terminal SSE event. The browser then reported the generic disconnect message even though the backend had reached a known timeout state.

### Fixes

- Added `medication_candidates_extracted` to the frontend SSE event allow-list.
- Added a frontend regression test proving candidate events are delivered to the analysis hook boundary.
- Changed image extraction failures to emit a failed `extracting` stage before the terminal error event.
- Added a precise `PROVIDER_CONFIGURATION_REQUIRED` message when the vision backend is absent because its server-side credentials are not configured.
- Added a terminal `CONFIRMATION_TIMEOUT` event and failed `confirming` stage update when confirmation expires.
- Marked terminated image requests as finished so the route cleanup can remove them from `pending_analyses`.
- Removed raw HTTP response bodies and network exception text from vision-provider errors.
- Added an API regression test proving missing vision configuration produces a terminal structured error rather than an unexplained stream close.

### Verification

- `$env:TESTING='1'; uv run pytest -q tests/providers/test_vision_backend.py tests/api/test_prescription_vision_e2e.py tests/e2e/test_v6_c6_image_confirmation_rxnorm.py tests/test_model_selector.py`: **33 passed, 6 warnings**.
- `$env:TESTING='1'; uv run pytest -q tests/api/test_prescription_vision_e2e.py tests/e2e/test_v6_c6_image_confirmation_rxnorm.py`: **7 passed, 6 warnings**.
- `$env:TESTING='1'; uv run pytest -q`: **1,211 passed, 4 skipped, 513 warnings**.
- `Set-Location frontend; npm run test -- --run`: **4 files, 20 tests passed**.
- `Set-Location frontend; npx --no-install tsc --noEmit`: **passed**.
- `Set-Location frontend; npm run build`: **passed**.
- `uv run ruff check src/ tests/`: **passed**.
- `uv run bandit -r src --ini .bandit -q`: **passed**.
- `gitleaks detect --no-banner --redact`: **no leaks found**.
- `git diff --check`: **passed**.
- A local deterministic service check with no vision backend produced `stage_update(status=failed)` followed by `error(code=PROVIDER_CONFIGURATION_REQUIRED)` and marked the request finished.

All validation used deterministic mocks or local configuration checks. No external vision-provider request was issued. The environment still has no configured `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CLOUDFLARE_API_TOKEN`, or `OPENAI_API_KEY`, so real prescription-image extraction remains **Not Verified / Blocked by provider configuration**.

### User-facing behavior

With no configured vision provider, the expected result is now an extraction-stage failure explaining that server-side credentials are required, rather than a generic stream-disconnect message. With a configured provider, the expected sequence is candidate delivery, explicit user confirmation, RxNorm resolution, and the remaining evidence/safety pipeline. A live provider run is still required to verify that path end to end.

### Git integrity

Final repository identity before publication: root `C:/Users/sunny/.copilot/repos/copilot-worktrees/CASE STUDY/sandysunny99-bookish-meme`, branch `sandysunny99-implement-request`, pre-commit HEAD `91c853776ff7085faaaf25abdfbefa157dd55558`. The reviewed implementation was committed as `d101c63` (`fix: harden prescription analysis and history workflows`); this documentation update is committed separately after recording that implementation hash. The full-suite run regenerated frozen experiment/audit timestamps; those seven known generated files were restored byte-for-byte to HEAD and are not included in the commits. No force-push, reset, cleanup, merge, or branch switch was performed.
