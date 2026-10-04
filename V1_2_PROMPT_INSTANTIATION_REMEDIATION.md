# V1.2 Prompt Instantiation Remediation Report

## Problem
During the pre-execution audit for the formal V1.2 Real-LLM evaluation, the prompt instantiation preview crashed with `KeyError: '\n  "conclusion"'`. 

## Root Cause
The evaluation harness (or preview script) attempted to instantiate the frozen V1.2 prompt template using Python's standard `str.format()` mechanism. The V1.2 prompt template legitimately includes literal single curly braces `{...}` to describe the expected structured JSON output format. Python's `.format()` interpreter misidentified these JSON syntax braces as missing template placeholders.

## Frozen Artifact Status
The frozen prompt `experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt` must remain immutable. Mutating the prompt to escape the braces (e.g., `{{ "conclusion" }}`) would violate the protocol's hash freeze and protocol immutability guard.

## Harness Change
A new deterministic string replacement module was created at `experiments/real_llm_evaluation/prompt_instantiator.py`. This mechanism explicitly and solely replaces the four V1.2 declared placeholders:
1. `{query}`
2. `{patient_context}`
3. `{risk_tier}`
4. `{evidence_block}`

Literal JSON braces are safely ignored. Missing or unexpected placeholders trigger explicit `ValueError` exceptions, preventing silent failures.

## Artifact Hashes
- **Prompt Hash Before:** `e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c`
- **Prompt Hash After:** `e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c` (UNCHANGED)
- **Dataset Hash:** `db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc` (UNCHANGED)
- **Protocol Status:** UNCHANGED (V1.2 remains active)

## Tests Performed
A test suite `test_v1_2_prompt_instantiation.py` was implemented to validate:
- **Non-Sent Validation:** Confirmed prompt instantiated correctly without crashing.
- **Literal Brace Preservation:** JSON syntax remained intact.
- **Cross-Case Isolation:** Verified requests do not bleed context.
- **Arm Symmetry:** Verified prompt output is identical across theoretical arms before specific post-gates apply.

## Research Requests
Total real LLM medical research requests executed during remediation: 0.

## Remaining Blockers
None. The harness defect is resolved. The V1.2 protocol remains perfectly frozen. Waiting on researcher authorization to execute the 160 planned medical requests.
