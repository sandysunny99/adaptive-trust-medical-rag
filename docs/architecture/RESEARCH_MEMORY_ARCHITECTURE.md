# Research Memory Architecture

**Phase 11**

## Separation Invariant

```
Scientific Evidence  ≠  Agent Context  ≠  Research Memory
```

- **Scientific Evidence**: Actual pharmacology documents. Lives in the corpus.
- **Agent Context**: Temporary task/session context (Phase 10).
- **Research Memory**: Persistent, durable history of sessions, experiments, decisions, and failures. (Phase 11).

## Semantic Claims

**Memory can:**
- preserve historical observations
- preserve decisions
- preserve failures
- preserve session state
- reference experiments/evidence

**Memory cannot:**
- become evidence
- change trust weights
- change retrieval configuration
- change experiment configuration
- change approval state
- execute instructions
- grant permissions
- mutate canonical artifacts

## Security & Integrity Boundary

Stored memory is treated strictly as **DATA**, enforcing a strict **instruction/data boundary**. Memory is stored as inert data and does not execute instructions.

## Provenance Enforcement

Every `MemoryRecord` requires a valid provenance dictionary. The architecture strictly verifies:
- Provenance exists and is a dictionary.
- Provenance contains a meaningful origin/reference field (`source`, `origin`, or `reference`).

The underlying `ResearchMemoryStore` stores a deep copy of all records and provenance data upon insertion, ensuring that down-stream mutability by an agent does not alter the historical record.

## Determinism

- **Deterministic serialization**: YES (JSON with sorted keys)
- **Stable ordering**: YES where applicable
- **UUID-based record creation**: Intentionally nondeterministic (reproducible experiments must use explicit experiment/run IDs as provenance)
