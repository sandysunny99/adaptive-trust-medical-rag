# Phase 13C: Caseset Review V2 (Reviewed Candidate)

**Generated From:** `scratch/generate_v2_reviewed.py`
**Candidate File:** `experiments/security_evaluation/security_cases_v2_reviewed.jsonl`
**Previous Candidate Hash (v2):** `8be4c7c1ea500590cebdcc0b54524850412cf1a588946359242e976ac664890b`
**Reviewed Candidate Hash:** `9ca45a39d16bb7b84a4d20fdb74991940e28c807576b7997a4d3a5ff12eb5a69`

## Taxonomy Coverage

### PROMPT_INJECTION
- DIRECT_INSTRUCTION: **PRESENT** (4 cases)
- ROLE_OVERRIDE: **PRESENT** (4 cases)
- SYSTEM_IMPERSONATION: **PRESENT** (4 cases)
- TOOL_INVOCATION: **PRESENT** (4 cases)
- PRIVILEGE_ESCALATION: **PRESENT** (4 cases)
- CONTEXT_MANIPULATION: **PRESENT** (4 cases)
- MEMORY_INJECTION: **PRESENT** (3 cases)
- EVIDENCE_INJECTION: **PRESENT** (3 cases)

### RETRIEVAL_POISONING
- MISSING_PROVENANCE: **PRESENT** (3 cases)
- INVALID_PROVENANCE: **PRESENT** (3 cases)
- SUSPICIOUS_METADATA: **PRESENT** (3 cases)
- IDENTITY_MISMATCH: **PRESENT** (3 cases)
- AUTHORITY_MANIPULATION: **PRESENT** (4 cases)
- METADATA_INJECTION: **PRESENT** (3 cases)
- SOURCE_CONFLICT: **PRESENT** (5 cases)
- AUTHORITATIVE_IMPERSONATION: **PRESENT** (3 cases)

### BOUNDARY_VIOLATION
- EVIDENCE_CONTROL_ATTEMPT: **PRESENT** (4 cases)
- CONTEXT_TOOL_ATTEMPT: **PRESENT** (4 cases)
- MEMORY_TOOL_ATTEMPT: **PRESENT** (4 cases)
- MEMORY_TRUST_MUTATION: **PRESENT** (4 cases)
- MEMORY_EXPERIMENT_MUTATION: **PRESENT** (3 cases)
- CONTEXT_AUTHORIZATION_MUTATION: **PRESENT** (3 cases)
- EVIDENCE_PERMISSION_ESCALATION: **PRESENT** (3 cases)

### PROVENANCE_ATTACK
- SOURCE_ID_MISSING: **PRESENT** (2 cases)
- SOURCE_ID_FABRICATED: **PRESENT** (2 cases)
- SOURCE_CONFLICT: **PRESENT** (5 cases)
- REFERENCE_UNVERIFIABLE: **PRESENT** (1 cases)
- PROVENANCE_REPLACEMENT: **PRESENT** (2 cases)
- PROVENANCE_LOSS: **PRESENT** (1 cases)

### BENIGN_CONTROL
- NORMAL_EVIDENCE: **PRESENT** (5 cases)
- NORMAL_METADATA: **PRESENT** (3 cases)
- NORMAL_MEMORY: **PRESENT** (3 cases)
- NORMAL_EXPERIMENT: **PRESENT** (2 cases)
- QUOTED_INSTRUCTION_TEXT: **PRESENT** (4 cases)
- NORMAL_TECHNICAL_LANGUAGE: **PRESENT** (3 cases)

## Duplicate Review
- **Total Generated:** 110
- **Exact Payload Duplicates:** 0
- **Genuinely Distinct Mechanisms:** Each case uses unique payload text, varying attack mechanism, location, target, and structural form.
- **Template Clusters:** None detected. Cases are individually authored with distinct scenarios.

## Target/Subtype Consistency
- **Inconsistencies Found:** 0

## Authorization Property Review
- **Authorization-Attempt Cases:** 26
- **Issues Found:** 0

## Provenance Property Review
- **Provenance-Required Cases:** 27
- **Issues Found:** 1
  - SEC_V2_083: PROVENANCE_ATTACK with seemingly valid provenance

## Implementation Leakage Review
- **Detector Phrases Checked:** 27
- **Hits Found:** 1
  - SEC_V2_102: contains detector phrase 'ignore all previous'

## Power/Sample Size Update
- **Primary Endpoint:** UAR (Unauthorized Action Rate)
- **Authorization-Attempt Cases (n):** 26
- **Assumptions:** Baseline UAR ~100%, Hardened UAR <10%, discordance ~90%
- **Effective Paired n:** 26
- **Note:** With n=26 and expected high discordance, McNemar's test retains reasonable power (>80%) to detect absolute differences of >=40% at alpha=0.05. However, this is smaller than the original n=25 design target. The reduction is justified: only genuine authorization-attempt cases enter the UAR denominator.

## Status
- **Taxonomy Coverage:** ALL SUBTYPES PRESENT
- **DATASET_READY_FOR_REVIEW:** YES
- **DATASET_FROZEN:** NO (Pending manual review)
- **SECURITY_EVALUATION_READY_FOR_APPROVAL:** NO
