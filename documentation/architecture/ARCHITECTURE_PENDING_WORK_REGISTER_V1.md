# ARCHITECTURE_PENDING_WORK_REGISTER_V1

| ID | Pending Item | Why Pending | Required Evidence | Blocker | Next Action |
|---|---|---|---|---|---|
| ARCH-P01 | API runtime verification | APIs only exist as code/planned, not executed in runtime. | Live HTTP trace to NCBI/FDA. | Credential/Network policies | Implement API execution tests |
| ARCH-P02 | Actual evidence acquisition path | System relies heavily on frozen snapshot. Live query not E2E validated. | E2E trace of query -> API -> graph. | Missing API logic | Decide if Live is required for Phase 1 |
| ARCH-P03 | Trust component verification | Missing values might default to 0 without protocol override. | Unit tests proving MISSING != ZERO behavior. | TrustScorer implementation limits | Audit TrustScorer missing-value paths |
| ARCH-P04 | Security validation classification | Generative E2E is unverified. | End-to-end LLM runs with adversarial prompts. | Live LLM Provider | Execute live security benchmark |
| ARCH-P05 | Claim/citation/answer-safety implementation | Verification layer components are mostly PLANNED/CODE_PRESENT. | AnswerSafetyGate integration in Orchestrator. | Implementation incomplete | Write AnswerSafetyGate |
| ARCH-P06 | Live provider transport | REAL_PROVIDER_TRANSPORT = NOT_EXECUTED. | Valid 200 OK from Groq/Cloudflare. | API Credentials | Provision keys and run transport test |
| ARCH-P07 | Model/revision verification | Models not validated on live endpoints. | Model name trace in live payload. | P06 | Run model identity test |
| ARCH-P08 | Structured-output verification | NATIVE_JSON_SCHEMA not tested against real endpoints. | Live provider JSON schema accept. | P06 | Test JSON Schema live |
| ARCH-P09 | Execution configuration freeze | Blocked by missing live verification. | TRACK_A_LLM_EXECUTION_CONFIG marked FROZEN. | P06-P08 | Freeze configuration |
| ARCH-P10 | 8-case medical LLM pilot | Config not frozen. | 8 Pilot annotations generated. | P09 | Run Medical Pilot |
| ARCH-P11 | Track A remaining annotation | Pilot not evaluated. | P11-P60 annotations generated. | P10 | Run Batch |
| ARCH-P12 | Full benchmark unlock | Pending Track A completion. | RAGAS/DeepEval executed. | P11 | Run Benchmark |
