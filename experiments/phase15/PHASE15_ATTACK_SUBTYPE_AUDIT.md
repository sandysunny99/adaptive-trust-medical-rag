# PHASE 15 ATTACK SUBTYPE AUDIT

## Subtype Distribution
- **Total semantic subtypes:** 171
- **Cases per subtype:** 1 (each case represents a uniquely identified attack mechanism or pharmacological claim type, except Benign Controls which are 30 cases labeled 'none').

## Semantic Validity
No artificial identifiers (e.g., `type_01`) were used. Every subtype name encodes a genuine attack mechanism or error class. 

### Examples by Family
**PROMPT_INJECTION**
- `instruction_override_multilingual`
- `hidden_instruction_html`
- `role_manipulation`
- `token_smuggling`

**RETRIEVAL_POISONING**
- `authority_inflation`
- `dose_falsification`
- `contraindication_removal`
- `temporal_manipulation`

**BOUNDARY_VIOLATION**
- `trust_config_modification`
- `evidence_deletion`
- `system_invocation_by_evidence`
- `escalate_principal`

**UNSUPPORTED_CLAIM**
- `fabricated_ddi`
- `false_bioequivalence`
- `unproven_combination`
- `fabricated_reversal`

**CONTRADICTION**
- `dose_response_conflict`
- `guideline_conflict`
- `surrogate_vs_clinical_conflict`
- `meta_analysis_conflict`

## Conclusion
The 171 distinct attack subtypes represent genuine, highly granular security distinctions, not inflated labeling.
