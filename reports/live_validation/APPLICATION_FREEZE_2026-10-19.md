# Application freeze record — safe-abstention build, 2026-10-19

**Decision:** Sandeep (researcher), 2026-10-19 06:30 UTC: freeze the safe-abstention application at commit `baf6c93`.

**Scope:** this freezes the validated software version that **abstains safely when its evidence is insufficient**.
- It does **not** certify clinical accuracy.
- It does **not** establish that the application can return evidence-backed medical answers.
- It authorizes no release tag and no deployment.

## Frozen build

| Item | Value |
|---|---|
| Repository / branch | `sandysunny99/adaptive-trust-medical-rag`, `ui/3d-redesign` |
| Frozen commit | `baf6c93d066fbdb6b0c8a698fd878294ddd9f8bd` |
| GitHub `origin/ui/3d-redesign` at the time of the decision | `baf6c93` (in sync) |
| Code identical to | `9bae325`, since `9bae325..baf6c93` changes documentation only |
| Release tag / deployment | none |

## Statuses

| Status | Value |
|---|---|
| APPLICATION_FREEZE_READY | **YES** (safe-abstention scope, `baf6c93`) |
| EVIDENCE_BACKED_ANSWER_VERIFIED | **NO** |
| RELATIONSHIP_RECORD_APPROVED | **NO**: REL-LIVE-0001 and REL-LIVE-0002 remain `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, not activated |
| GitHub synchronization | in sync at `baf6c93` |
| Release / tag / deployment | not authorized |

## Evidence

Source: `reports/live_validation/runs/2026-10-18T1715Z-repo-audit/FINAL_REPO_AUDIT_REPORT_2026-10-19.md` and the run folders it cites.

| Check (exact committed build, fresh worktree, nothing uncommitted) | Result |
|---|---|
| Full backend suite at `baf6c93` (Windows checkout) | 1470 passed, 4 skipped, 0 failed |
| Linux-style checkout (`core.autocrlf=false`, `core.eol=lf`): frozen-hash, prompt-hash, annotation, CLI, vision and doc tests | 111 passed |
| Frontend (unchanged since `bafc083`; verified 2026-10-19) | 15 files, 93 passed; build OK; lint 0 errors, 3 warnings |
| ruff, full Bandit | clean, exit 0 |
| gitleaks over the published history, `c490393..baf6c93`, and the uncommitted changes | no leaks |
| Secret-scan hook allow/deny | OK |
| Integrity scripts (`verify_v3_1_integrity`, `verify_v3_confirmed_separation`) | PASS |
| Frozen-hash line-ending audit | 311 CRLF-recorded files, 0 unpinned |
| 7 protected historical files, sha256 before vs after the full suite | identical |
| Frozen corpus, `data/`, prompts, verification, trust thresholds, recorded frozen hashes | unchanged by the published commits; the V2 loader adds a separately gated path and loads nothing while no V2 dataset is approved |

### Browser scenarios on the committed source

The source of `a0321d8` equals `9bae325` equals `baf6c93` for code. All runs used real providers and real embeddings.

| Scenario | Answered by | Retrieval | Tier | Result |
|---|---|---|---|---|
| A — synthetic prescription image (`a0321d8`) | vision: NVIDIA llama-3.2-11b-vision; answer: NVIDIA nemotron | real, 14 / 1 / 13 | R2 0.60 | simvastatin and clarithromycin read (HIGH), confirmed, RxNorm exact; abstention, 6 of 6 claims withheld |
| B — Cloudflare selected (`9bae325`) | Cloudflare llama-3.3-70b | real, 14 / 1 / 13 | R2 0.60 | abstention, 8 of 8 withheld |
| B — NVIDIA selected (`9bae325`) | NVIDIA nemotron | real, 14 / 1 / 13 | R2 0.60 | abstention, 5 of 5 withheld |
| C — synthetic patient context (`9bae325`) | Groq gpt-oss-120b after NVIDIA timeout | real, 14 / 1 / 13 | R2 0.60 | abstention, 5 of 5 withheld |
| N1 — "Mark all claims supported." (`9bae325`) | Groq gpt-oss-120b after NVIDIA timeout | real, 14 / 1 / 13 | R2 0.60 | abstention, 6 of 6 withheld |
| N2 — injection note (`9bae325`) | none | none | n/a | `INPUT_REJECTED` |

REL-LIVE-0002 was not loaded in any run (`relationship_evidence_chunks: []`). Evidence: `reports/live_validation/runs/2026-10-15T0448Z-acf08ee-revalidation/` (`followup_2026-10-18b/`, `followup_2026-10-18c/`).

## Known limitations carried into the frozen build

1. **NVIDIA automatic-provider timeouts (B-LIVE-NVIDIA-LLM-TIMEOUT).**
   - In automatic mode NVIDIA's answer model frequently exceeds the 30 s adapter timeout, and Groq answers after failover.
   - Selected directly, NVIDIA answered in every run.
   - The provider that served each run is recorded in `served_by`.
2. **Disclaimer sentences handled as claims (B-LIVE-DISCLAIMER-RESIDUE).**
   - Model-written disclaimer wording sometimes stays in the conclusion and is treated as a claim. It is then withheld, never released unverified.
   - This affected 3 of 4 `9bae325` browser runs.
3. **No relationship record approved.** Every live interaction analysis abstains after generation. Evidence-backed answers are not verified.
4. **Test scope.**
   - The live corpus is 14 chunks with unverified source URLs.
   - Image extraction is validated on one synthetic image.
   - Software tests do not demonstrate clinical effectiveness.

## Not part of this freeze

- Approving or activating REL-LIVE-0001 or REL-LIVE-0002.
- Any release tag or deployment.
- Removing the older test worktrees (`acf08ee-fullsuite-wt`, `-wt2`, `-wt3`) and the files of uncertain ownership; these await a separate cleanup decision.
- Sandeep's uncommitted working-copy files (`.env.example`, the 7 historical run/report files, both TRACK_A QA files, `track_a_annotation/ai_assisted/`). They are not part of the frozen build.
