# P0 ADVERSARIAL CITATION TEST
- **Claim**: "Drug A is associated with Event X [Source 5]."
- **Source 1**: Supports claim.
- **Source 5**: Unrelated (neutral).
- **Result**: `citation_supports` is `False`. The global state is overridden by the provenance rule, and `FinalSupportState.UNSUPPORTED` is correctly assigned.
