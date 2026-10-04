# PROVENANCE END-TO-END AUDIT

- Source -> Document -> Chunk: PRESENT (via `metadata` in retrieval).
- Chunk -> EvidenceChunk: PRESENT (Orchestrator maps `chunk_id`).
- EvidenceChunk -> Claim: **BROKEN (PROVENANCE_GAP)**.

While the LLM output generates `[Source N]` and it is parsed into `citation_ids`, the `ClaimVerifierV2` uses a global maximum (`max_ent`) across ALL session chunks to approve a claim. A claim citing `[Source 2]` can be marked `SUPPORTED` purely because `Chunk 1` entails it. The gating logic ignores `citation_resolves` and `citation_supports_claim`.
