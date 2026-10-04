# Baseline Protocol Hierarchy

## Document Classifications

| Document | Classification | Intent / Role |
|---|---|---|
| `experiments/architecture_baseline/FREE_REPLICATION_V1_PROTOCOL.md` | **NORMATIVE_PROTOCOL** | Defines the experiment evaluating LLM generation fallback behavior. |
| `experiments/architecture_baseline/FREE_REPLICATION_V1_CONFIG.json` | **EXPERIMENT_MANIFEST** | Specifies runtime parameters (LLM provider, model) for the replication experiment. |
| `docs/ARCHITECTURE.md` | **DESCRIPTIVE_ARCHITECTURE** | High-level technical specification of database schemas, gates, and components. |
| `experiments/phase14/PHASE14_ARCHITECTURE.md` | **DESCRIPTIVE_ARCHITECTURE** | Documents the multi-agent routing resilience features introduced in Phase 14. |
| `experiments/architecture_baseline/CURRENT_ARCHITECTURE_SNAPSHOT.md` | **IMPLEMENTATION_SNAPSHOT** | A point-in-time capture of the codebase state as of commit `8741f59`. Not a normative protocol. |
| `experiments/runs/fusion-evaluation-v3-real/manifest.json` | **HISTORICAL_RECORD** | A serialized experiment run manifest proving what models were actually executed. |

## Normative vs Descriptive

1. **Normative Protocol** (`FREE_REPLICATION_V1_PROTOCOL.md`): This document governs the experiment. However, it explicitly focuses on the generation tier (Groq vs standard LLM). It is completely silent on the retrieval baseline, including the semantic embedding model.

2. **Descriptive Architecture** (`docs/ARCHITECTURE.md`): Specifies that `evidence_chunks` requires a `VECTOR(768)` data type. While normative for database structure, it is a technical spec rather than an experimental authorization.

3. **Implementation Snapshot** (`CURRENT_ARCHITECTURE_SNAPSHOT.md`): Although it lists `SimpleEmbeddingModel`, it is explicitly a snapshot of current implementation constraints rather than a protocol authorization.

## Conclusion

The normative research protocol **does not explicitly authorize** any specific semantic embedding model for the Gate 5 evaluation.

`evidence_source`: `manual_analysis`
