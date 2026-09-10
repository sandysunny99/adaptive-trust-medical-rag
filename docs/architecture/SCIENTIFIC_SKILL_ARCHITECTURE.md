# Scientific Skill Architecture

**Phase 9: Skill Surface**

This document describes the design pattern and boundaries of the project's scientific skill surface. The purpose of this layer is to expose existing robust pharmacological RAG capabilities to autonomous agent orchestrators (and future phases like the OpenViking Context Engine) without duplicating any underlying scientific logic.

## Design Philosophy

The architecture explicitly enforces:
```text
Agent
  ↓
Skill Registry (registry.json)
  ↓
Skill Wrapper (skill.py + SKILL.md)
  ↓
Existing Project Module (e.g., AdaptiveTrustScorer)
  ↓
Structured Result
  ↓
Provenance
```

## Why Thin Wrappers?
We chose a "thin wrapper" design to ensure that the skill surface **does not duplicate core logic**. 
1. **Single Source of Truth**: The pharmacological evaluation logic, trust scoring, and retrieval mechanics remain exactly where they were validated during the earlier phases.
2. **Experiment Isolation**: We can run automated tests against the skills without inadvertently mutating the frozen Phase 2F.5B annotation experiment or the F0/F3 retrieval caches.
3. **Safe Dispatch**: Wrappers guarantee that even if an agent hallucinates malformed inputs, the system fails closed gracefully, catching exceptions and returning standardized `SkillOutput` with explicit provenance.

## Provenance Guarantee
Every `SkillOutput` preserves the lineage of evidence. Wrappers automatically inject metadata regarding execution timestamp, invoked module, wrapper version, and preserve any document/source identities returned by the underlying module. This ensures that down-stream answer-safety gates can still accurately trace claims back to their source, adhering strictly to Project Rule §2 (Evidence Grounding).
