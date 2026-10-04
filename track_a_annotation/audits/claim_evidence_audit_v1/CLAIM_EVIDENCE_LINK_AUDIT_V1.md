# CLAIM-EVIDENCE LINK AUDIT

- **Mechanism**: LLM generated `[Source N]` mapped to `AtomicClaim.citation_ids`. This maps to `EvidenceChunk.citation_index`.
- **Are links unique/deterministic?**: Yes, via regex.
- **Are they verifiable?**: Yes, `CitationValidation` checks if they resolve and support.
- **GAP**: The link is *audited* but *ignored*. `ClaimVerifierV2.verify` uses a global session `max_ent` across ALL chunks to determine `support_state`. The specific `citation_validation.citation_supports_claim` boolean is created but explicitly excluded from the `GateDecision` logic.
