# TRUST INTERACTION
- Trust is scored *per candidate chunk*.
- Trust < Threshold -> Chunk filtered from context.
- If all chunks filtered -> Pre-Gen Abstention.
- If some chunks survive -> LLM Context built.
- Trust metadata propagates to `ClaimVerifierV2` via `EvidenceChunk`.
