# Context Engine Architecture

**Phase 10**

## Separation Invariant

```
Scientific Evidence  ≠  Agent Context  ≠  Research Memory
```

- **Scientific Evidence**: actual pharmacology documents from adapters (PubMed, EuropePMC, openFDA, RxNorm). Lives in the corpus. Never touched by the Context Engine.
- **Agent Context**: temporary context assembled for one query session. Lives in `SessionContext`. Discarded after session.
- **Research Memory**: persistent agent/research experience and decisions. Separate module (Phase 11).

## Architecture

```
Agent
  ↓
SessionContext (session-scoped, isolated)
  ├── ContextStore      L0 / L1 / L2 records with mandatory provenance
  ├── ResourceManager   typed references to evidence/skills/research
  └── RetrievalTrace    append-only observable decision log

  ↓
Scientific Evidence (via existing adapters, trust scorer, orchestrator)
  ↓
Trust (AdaptiveTrustScorer — Context Engine DISPLAYS, never COMPUTES)
  ↓
Verification (AnswerSafetyGate, claim_verifier — unchanged)
```

## Context Levels

| Level | Purpose |
|-------|---------|
| L0 | Short abstract / relevance snippet |
| L1 | Structured overview: title, source, entities, provenance, freshness, trust metadata |
| L2 | Full evidence text |

L0/L1 must be derived from the underlying evidence. They must not synthesize new pharmacological facts.

## Security Boundary

Evidence text stored in `ContextRecord.content` is treated as **data**, never as instructions. The `ContextStore` never evaluates, executes, or interprets content.

## Trust Boundary

`SessionContext.trust_metadata` stores trust scores produced by `AdaptiveTrustScorer`. The Context Engine has no trust-computation logic.
