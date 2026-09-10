# Security Evaluation Architecture

## Evaluation Data Flow

`mermaid
graph TD
    subgraph EVALUATION INFRASTRUCTURE
        Case[SecurityCase]
        Adapter{Condition Adapter}
        Metric[Security Metric Engine]
        Manifest[Research Harness / Manifest]
    end
    
    subgraph CONTROL PLANE [TRUSTED]
        Hardened[Phase 12 Security Extensions]
    end
    
    subgraph DATA PLANE [UNTRUSTED]
        Baseline[Existing Pipeline (Passthrough)]
    end
    
    Case --> Adapter
    Adapter -->|HARDENED| Hardened
    Adapter -->|BASELINE| Baseline
    
    Hardened --> Decision[Security Decision]
    Baseline --> Decision
    
    Decision --> Result[Result Schema]
    Result --> Metric
    Metric --> Manifest
`

#### 4. Evaluation Process (Phase 13)

The evaluation process guarantees isolated and deterministic execution.

#### Phase 13A (Forensic Pilot)
The initial exploratory run (`phase13a_exec_1`) was a 7-case pilot used to validate harness mechanics. It is classified as **FORENSIC / INVALID FOR SCIENTIFIC INFERENCE** and is excluded from scientific analysis.

#### Phase 13B (Scientific Design)
Current Phase: **DEVELOPED=YES, INTEGRATED=NO, VALIDATED=NO**
The scientific evaluation dataset (`security_cases_v2.jsonl`) and statistical analysis plan are undergoing design and freeze prior to execution. The primary endpoint will be Unauthorized Action Rate (UAR) evaluated via paired McNemar analysis.

#### Phase 13C (Future Execution)
When approved, execution will strictly follow the paired pipeline:
1. **Case Instantiation:** Generate `SecurityCase` from the frozen taxonomy.
2. **Parity Check:** Enforce `baseline.case_input_hash == hardened.case_input_hash`.
3. **Condition Adapter Routing:** Send case to BASELINE (Phase 12 bypassed) and HARDENED (Phase 12 active).
4. **Metric Generation:** Calculate ADR, ABR, FPR, UAR, and PPR based on explicit denominator properties.
5. **Statistical Reporting:** Generate paired statistical analysis under the locked plan.

## Boundaries
- **TRUSTED CONTROL**: Security Extensions (PromptInjectionDetector, RetrievalPoisoningDetector, AuthorizationBoundary).
- **UNTRUSTED DATA**: The synthetic payloads defined in the SecurityCase.
- **EVALUATION INFRASTRUCTURE**: The components managing parity, baseline vs hardened dispatch, metric calculations, and manifest generation.


## Phase 13C Human Review Infrastructure
- **Status**: DEVELOPED=YES, INTEGRATED=NO, VALIDATED=NO
- **Function**: Audits the genuine human review of candidate cases. Blocks freeze until complete.
