# Security Evaluation Protocol

Phase 13 defines and validates the evaluation infrastructure.
It does not execute the scientific security evaluation.

## 1. Objective

Compare the security boundary robustness of BASELINE vs HARDENED
configurations against prompt injection, retrieval poisoning, and
control-plane boundary violations.

## 2. Evaluation Unit

The `SecurityCase` dataclass containing:
- `case_id`, `attack_family`, `attack_subtype`, `payload`
- `target_component`, `expected_security_property`, `expected_outcome`
- `provenance_fixture`, `requested_action`, `metadata`
- `requires_provenance_preservation` (explicit denominator flag for PPR)
- `requires_authorization_check` (explicit denominator flag for UAR)
- `case_input_hash` (deterministic SHA-256 fingerprint of all input fields)

## 3. Attack Taxonomy

- PROMPT_INJECTION
- RETRIEVAL_POISONING
- BOUNDARY_VIOLATION
- PROVENANCE_ATTACK

## 4. Benign Controls

- BENIGN_CONTROL (Normal evidence, normal session memory, quoted
  instruction text). Used to measure False Positive Rate.

A BENIGN_CONTROL case does NOT automatically imply provenance
preservation or authorization checking. Those properties are set
explicitly per case.

## 5. Baseline Definition

The BASELINE condition is a **security-boundary adapter** representing
the absence of the Phase 12 security-extension decision layer.

It is NOT a complete re-execution of a historical unprotected RAG
pipeline. The experiment measures the **incremental contribution of
Phase 12 security-boundary mechanisms**, not complete end-to-end RAG
security.

Any underlying security behavior (e.g., `security/sanitizer.py`) that
necessarily exists in the baseline is documented as shared logic.

## 6. Hardened Definition

The HARDENED condition explicitly invokes Phase 12 Security Extensions:
- `PromptInjectionDetector`
- `RetrievalPoisoningDetector`
- `AuthorizationBoundary`

## 7. Metrics

All denominators are **case-property based**, not inferred from attack family.

- **Attack Detection Rate (ADR)**: Detected Attacks / Total Attacks
  (denominator: `attack_family != BENIGN_CONTROL`)
- **Attack Block Rate (ABR)**: Blocked Attacks / Total Attacks
  (denominator: same as ADR)
- **False Positive Rate (FPR)**: Flagged Benign / Total Benign
  (denominator: `attack_family == BENIGN_CONTROL`)
- **Unauthorized Action Rate (UAR)**: Accepted Actions / Authorization Attempts
  (denominator: `requires_authorization_check == True`)
- **Provenance Preservation Rate (PPR)**: Preserved / Required
  (denominator: `requires_provenance_preservation == True`)

Zero denominators return `None` / undefined. Never silently return 0%.

## 8. Outcome Definitions

- `ALLOW`: Content passes security gates.
- `BLOCK`: Content is blocked by security gates.
- `FLAG`: Content is detected but not hard-blocked.
- `UNAUTHORIZED_ACTION_REJECTED`: Action is blocked by authorization policy.

## 9. Case Inclusion/Exclusion Rules

All structured cases matching the taxonomy are included. Unparseable
or corrupted fixtures are excluded.

## 10. Case Parity Rule

BASELINE and HARDENED must receive identical `case_input_hash` values
for the same `SecurityCase`. The hash covers all input fields including
`payload`, `provenance_fixture`, `requires_provenance_preservation`,
`requires_authorization_check`, `metadata`, and `requested_action`.

## 11. Reproducibility Rule

All results are deterministically serialized (`json.dumps(sort_keys=True)`)
and tracked via the existing `RunManifest` / artifact registry.

## 12. Failure Handling

Cases resulting in system crashes map to a separate error state and are
excluded from the denominator.

## 13. Approval Requirement

Evaluation execution requires the `SECURITY_EVALUATION_READY_FOR_APPROVAL`
gate to be explicitly satisfied.

## 14. No-Mid-Experiment-Modification Rule

Condition adapters and metric definitions are FROZEN once the experiment
begins.

## 15. Statistical Analysis Contract

STATISTICAL METHOD = TO BE LOCKED BEFORE EXPERIMENT EXECUTION.

Future analysis will be delegated to `statistical_report.py` (e.g.,
McNemar paired analysis where appropriate).

Do not lock the final statistical method until the actual evaluation
dataset/design is frozen.
