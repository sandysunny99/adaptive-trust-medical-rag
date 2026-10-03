# P0 MULTI CITATION TEST
- **Claim**: "Drug A is supported [Source 1][Source 5]."
- **Sources**: 1 supports, 5 is neutral.
- **Result**: Existing project logic calculates max entailment and max neutral across all cited chunks. Since max neutral across all cited chunks is 1.0 (from Source 5), `citation_supports` evaluates to `False`. The claim becomes `UNSUPPORTED`. This exposes a multi-citation policy gap in the existing semantic design, but honors the legacy requirement.
