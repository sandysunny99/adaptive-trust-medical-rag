# Archive

Historical reports, audits and result files. Most sat at the repository root until the November 2026 cleanup;
they were moved here unchanged (`git mv`, so `git log --follow` shows their history). They record how the project
got to its current state and are kept for provenance. Current documentation is one level up, in `docs/`.

| Folder | Files | Contents |
|---|---|---|
| [`architecture_reviews/`](architecture_reviews/) | 107 | Architecture audits, gate decisions and research-status snapshots (formerly `documentation/architecture/`) |
| [`claim_verifier/`](claim_verifier/) | 30 | Claim-verifier v1/v2 specifications, audits, NLI sanity results and claim-evidence protocols |
| [`engineering_ci_and_audits/`](engineering_ci_and_audits/) | 26 | CI, GitHub-check, lint (ruff, Bandit) and test-suite audits; deployment notes; roadmap |
| [`gate5_pos02_research_controls/`](gate5_pos02_research_controls/) | 29 | Gate 5 execution and POS02 corpus amendment records; manifest-hash and research-control checks |
| [`live_app_and_providers/`](live_app_and_providers/) | 45 | Live-application reports: provider integration and health, failover, SSE, retrieval, safety |
| [`misc/`](misc/) | 1 | Other single reports |
| [`multimodal_v6/`](multimodal_v6/) | 32 | Prescription-image pipeline, multimodal security and the V6 checkpoint reports (C3 to C13) |
| [`prompt_injection/`](prompt_injection/) | 11 | Prompt-injection (statin) evaluation: method audits, matrices, metrics and results |
| [`real_llm_v1_2_v1_3/`](real_llm_v1_2_v1_3/) | 64 | Real-LLM evaluation protocols V1.2/V1.3, their results, forensic audits and raw result dumps |
| [`track_a_annotation/`](track_a_annotation/) | 33 | Track A relevance-annotation protocol, schemas, guides, QA and agreement records |

Some research scripts in `scripts/` read or write files here; their paths were updated in the same change.
