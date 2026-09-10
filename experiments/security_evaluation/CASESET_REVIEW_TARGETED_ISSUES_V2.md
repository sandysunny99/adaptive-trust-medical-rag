# Phase 13C: Caseset Review Targeted Issues V2

This report flags specific structural patterns that require particularly careful human inspection.
**These are REVIEW FLAGS only.** Do not automatically ACCEPT/REVISE/REJECT them.

### Priority 2: User Target Scope
*Cases: SEC_V2_005, SEC_V2_006, SEC_V2_007*
- **Flag**: USER target scope vs untrusted-data security boundary. The current evaluation is principally focused on evidence/context/memory injection. Check if these should be scoped out or if they accurately reflect the boundary test.

### Priority 3: UAR Interaction
*Cases: SEC_V2_013, SEC_V2_014, SEC_V2_015, SEC_V2_016, SEC_V2_017, SEC_V2_018, SEC_V2_019*
- **Flag**: Prompt Injection + authorization-flag interaction. These cases mix PROMPT_INJECTION with `requires_authorization_check=True`. The evaluation architecture routes PI to the PromptInjectionDetector, while AuthorizationBoundary handles UAR. Verify whether these should contribute to UAR or be explicitly routed/revised.

### Priority 4: Privilege Escalation Inconsistency
*Case: SEC_V2_020*
- **Flag**: PRIVILEGE_ESCALATION subtype but `requires_authorization_check=False` and no `requested_action`. Check if this should be a pure PI case or converted into a genuine authorization attempt.

### Priority 5: Metadata Injection Visibility
*Cases: SEC_V2_047, SEC_V2_048, SEC_V2_049*
- **Flag**: METADATA_INJECTION payload vs metadata fixture consistency. The malicious content is hidden in the metadata fixture, not the payload text. Verify the test actually challenges the boundary properly.

### Priority 6: Expected Outcome Mismatch
*Cases: SEC_V2_053, SEC_V2_054, SEC_V2_055*
- **Flag**: Expected security property states "FLAG" while expected outcome states "BLOCK". Verify whether the security policy dictates an absolute block for authoritative impersonation, or merely a verification/flag.

### Priority 7: Source Conflict Overlap
*Cases: SEC_V2_085, SEC_V2_086*
- **Flag**: SOURCE_CONFLICT expected outcome is BLOCK, but retrieval-poisoning SOURCE_CONFLICT cases (050-052) expect FLAG. Check if contradiction cases should behave differently from provenance-integrity failures.
