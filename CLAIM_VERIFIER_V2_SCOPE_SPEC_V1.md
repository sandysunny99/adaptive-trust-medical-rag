# CLAIM_VERIFIER_V2_SCOPE_SPEC_V1

## Overview
Defines how ClaimVerifierV2 preserves pharmacological qualifications and bounds, preventing NLI from endorsing overgeneralized claims.

## Explicit Qualifier Extraction
The verifier statically extracts known qualifiers from the evidence text:
- **interaction_scope**: e.g., "clinically significant"
- **mechanism_scope**: e.g., "pharmacokinetic", "pharmacodynamic"
- **observation_scope**: e.g., "observed", "reported", "studied"
- **polarity**: e.g., "no", "not"

## Scope Protection Rule
If the evidence is bounded negative (contains negative polarity + specific mechanism/interaction scopes), the verifier scrutinizes the hypothesis claim:
- If the hypothesis drops the mechanism/interaction scope (e.g., dropping "pharmacokinetic") AND asserts a universal or absolute state (e.g., "completely safe", "no interaction of any kind", "no meaningful interaction exists", "essentially no interaction"), the NLI entailment score is overridden.
- The state is forced to **UNSUPPORTED** (or **CONTRADICTED** if directly opposing).
- This explicitly prevents "No clinically significant PK interaction" from degrading into "The drugs are safe together."
