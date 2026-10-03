# EXECUTION PATH
1. Answer decomposed into `AtomicClaim`.
2. `[Source N]` parsed to `citation_ids`.
3. `ClaimVerifierV2` computes `chunk_evals` for ALL chunks.
4. `citation_resolves` checks if chunks match citations.
5. `citation_supports` checks if cited chunks specifically have `cit_ent > max(cit_con, neu)`.
6. Enforce block: If `citation_present` and not `citation_supports`, `state = UNSUPPORTED`.
7. `GateDecision` processes `state`.
