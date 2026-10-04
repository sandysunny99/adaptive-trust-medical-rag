# Real-LLM V1.1 Pre-Execution Methodology Audit

## Objective
READ-ONLY methodological audit to determine whether the frozen V1.1 protocol permits a scientifically symmetric comparison between ARM_A_BASELINE and ARM_B_ADAPTIVE.

## 1. Critical Audit & Circularity Check
- **ARM A**: Trust Control DISABLED, Abstention DEFAULT, Claim Verification DISABLED
- **ARM B**: Trust Control ENABLED, Abstention ENABLED, Claim Verification ENABLED
- **Circularity Risk**: **PRESENT**. If ARM B is scored by the same Claim Verification mechanism it uses internally as a control gate, while ARM A is not scored or scored differently, the comparison is asymmetric and circularly validates the control mechanism.
- **Solution Needed**: A common, frozen post-generation evaluator must be explicitly defined. Both ARM A's raw output and ARM B's final output must be passed through this detached evaluator to measure comparative generation-quality and evidence-grounding.

## 2. Metric Symmetry Status
| Metric | Status | Common Evaluator Available | Circularity Risk |
|---|---|---|---|
| claim_support_rate | ASYMMETRIC | YES (Detached ClaimVerifierV2) | PRESENT |
| citation_validation_rate | ASYMMETRIC | YES | PRESENT |
| unsupported_answer_rate | ASYMMETRIC | YES | PRESENT |
| abstention_rate | DESCRIPTIVE ONLY | N/A (Observed counts only) | NONE |
| provider_failure_rate | SYMMETRIC | YES | NONE |

## 3. Abstention Clarification
Confirmed that bstention_rate measures **OBSERVED_ABSTENTION_RATE** only. Due to the lack of answer-level ground truth in the 3_1_human_cases.json dataset, abstention correctness (whether the system *should* have abstained) cannot be computed.

## 4. Proposed Protocol Wording (For V1.2)
> "Runtime control mechanisms differ by experimental arm according to the defined integrated adaptive control-layer factor. For comparative generation-quality/evidence-grounding metrics, both arm outputs are evaluated using the same frozen post-generation evaluation procedure. Runtime claim verification in the adaptive arm is therefore a control mechanism, while common post-generation verification is the measurement mechanism."

## 5. Protected-State Audit
All protected artifacts (Track A, Benchmarks, Trust, Claim-Evidence, Controlled Abstention, Canonical Identity, RG-02, Phase 15, Historical Retrievals, Dataset, Protocol V1.1) are **UNCHANGED**.

## Conclusion
**PROTOCOL_REVISION_REQUIRED = TRUE**
**DATASET_AUTHORIZATION = PENDING_RESEARCHER_DECISION**
Execution remains UNAUTHORIZED. No LLM requests were executed.
