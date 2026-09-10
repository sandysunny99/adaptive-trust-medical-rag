# Phase 13B Security Evaluation: Case Set Design V2

## 1. Objective and Research Question

**Research Question:**
Does adding the Phase 12 security-boundary layer reduce unsafe security outcomes relative to the defined security-boundary baseline when both conditions receive identical adversarial and benign test cases?

*Note: This does NOT evaluate if the entire pharmacology RAG is secure, production-ready, or clinically safe. It evaluates the incremental security-boundary behavior of the Phase 12 extensions.*

## 2. Target Dataset Composition

**Total Target Cases: 110**

### Attack Family Allocation
* **PROMPT_INJECTION (30 cases):** 
  * Subtypes: DIRECT_INSTRUCTION, ROLE_OVERRIDE, SYSTEM_IMPERSONATION, TOOL_INVOCATION, PRIVILEGE_ESCALATION, CONTEXT_MANIPULATION, MEMORY_INJECTION, EVIDENCE_INJECTION.
* **RETRIEVAL_POISONING (25 cases):**
  * Subtypes: MISSING_PROVENANCE, INVALID_PROVENANCE, SUSPICIOUS_METADATA, IDENTITY_MISMATCH, AUTHORITY_MANIPULATION, METADATA_INJECTION, SOURCE_CONFLICT, AUTHORITATIVE_IMPERSONATION.
* **BOUNDARY_VIOLATION (25 cases):**
  * Subtypes: EVIDENCE_CONTROL_ATTEMPT, CONTEXT_TOOL_ATTEMPT, MEMORY_TOOL_ATTEMPT, MEMORY_TRUST_MUTATION, MEMORY_EXPERIMENT_MUTATION, CONTEXT_AUTHORIZATION_MUTATION, EVIDENCE_PERMISSION_ESCALATION.
* **PROVENANCE_ATTACK (10 cases):**
  * Subtypes: SOURCE_ID_MISSING, SOURCE_ID_FABRICATED, SOURCE_CONFLICT, REFERENCE_UNVERIFIABLE, PROVENANCE_REPLACEMENT, PROVENANCE_LOSS.
* **BENIGN_CONTROL (20 cases):**
  * Subtypes: NORMAL_EVIDENCE, NORMAL_METADATA, NORMAL_MEMORY, NORMAL_EXPERIMENT, QUOTED_INSTRUCTION_TEXT, NORMAL_TECHNICAL_LANGUAGE.

## 3. Case Independence and Duplicate Detection

Two cases are **NOT** independent if they merely paraphrase the same attack mechanism. 
* **Duplicate Detection Rules:** Automated detection for identical `payload`, canonicalized payload, `target`, `attack_subtype`, and `requested_action`.
* **Semantic Review:** Manual review to ensure distinct attack vectors, mechanisms, locations, privilege requests, or obfuscation levels. Replacing a single noun in a template does not create a new case.

## 4. Ground Truth and Outcome Labels

* **Independence:** Ground truth (`expected_outcome`) is frozen independently of the evaluated system and applies equally to BASELINE and HARDENED.
* **Valid Labels:**
  * `ALLOW`: Content passes security gates.
  * `BLOCK`: Content is blocked by security gates.
  * `FLAG`: Content is detected but not hard-blocked.
  * `ESCALATE`: Content triggers human review or high-alert.
  * `UNAUTHORIZED_ACTION_REJECTED`: Action blocked by authorization policy.

## 5. Explicit Case Properties

* **requires_provenance_preservation (bool):** Explicitly set to `True` for cases requiring provenance checks. Cannot be inferred solely from the attack family. Missing provenance must be intentionally designed, not accidentally omitted.
* **requires_authorization_check (bool):** Explicitly set to `True` only for genuine authorization attempts. Configuration-integrity attacks may have this set to `False` even if they are in BOUNDARY_VIOLATION.

## 6. Case Difficulty Levels

Difficulty reflects structural attack complexity, NOT the observed detector outcome.
* **LOW:** Direct instructions, clear boundary crossings, no obfuscation.
* **MEDIUM:** Contextual embedding, moderate obfuscation, indirect tooling attempts.
* **HIGH:** Complex privilege escalation, deep ambiguity, sophisticated metadata spoofing.

## 7. Attack/Control Balance and Leakage Prevention

* **Balance:** Benign controls must mirror attack structures (e.g., an unauthorized tool request vs. a legitimate informational request; prompt injection vs. quoted discussion of prompt injection).
* **Leakage Prevention:** Cases must not directly encode the exact regexes or heuristics of Phase 12 (e.g., `PromptInjectionDetector`). We are evaluating semantic boundaries, not regex pattern recognition.

## 8. BASELINE/HARDENED Input Parity

* Both conditions evaluate the **identical** case representation.
* A cryptographic `case_input_hash` (SHA-256) is computed over the fully instantiated `SecurityCase`.
* Evaluation is strictly rejected if `baseline.case_input_hash != hardened.case_input_hash`.

## 9. Review Requirements

Before case set generation is considered finalized (and before execution):
* **Dataset Review:** Must verify taxonomy coverage, semantic duplicates, implementation leakage, benign realism, expected-outcome consistency, provenance/authorization property correctness, and independence.
* **Case Set Freeze:** Upon approval, the dataset will be versioned (`security_cases_v2.jsonl`), hashed, and locked.
