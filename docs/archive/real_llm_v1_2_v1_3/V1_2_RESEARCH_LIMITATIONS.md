# V1.2 RESEARCH LIMITATIONS

- **Real-LLM Nondeterminism**: API-driven models may yield varying responses, though Temperature=0 mitigates this.
- **Provider Dependency & 50% Failure Rate**: Half of all requests resulted in a Provider Failure (specifically HTTP 429 Rate Limit from Groq). This severely reduces the effective sample size for generation quality.
- **Medical Answer Ground Truth Unavailable**: The evaluation relies on claim-level NLI contradiction/entailment against retrieved text, not against an absolute clinical truth standard.
- **Clinical Correctness Not Measured**: A "Supported" claim means it aligns with the retrieved text, but the retrieved text itself might be outdated or incomplete. Clinical correctness was not evaluated.
- **Frozen Historical Retrieval**: The retrieval step used a static snapshot, meaning dynamic real-time graph updates were not tested in this exact configuration.
- **Limited Sample Size**: Only 80 paired cases were processed, and due to rate limits, even fewer resulted in generated answers.
- **Arm B Abstention Overwhelming**: The evidence eligibility gate in Arm B abstained 90% of the time, meaning few to no LLM generation attempts were made in Arm B.
