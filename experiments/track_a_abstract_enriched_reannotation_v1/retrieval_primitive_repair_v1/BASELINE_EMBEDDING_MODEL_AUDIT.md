# Baseline Embedding Model Audit

## Implementation
`SimpleEmbeddingModel` is a 7-word toy fixture restricted to `['metformin', 'aspirin', 'warfarin', 'dosage', 'mechanism', 'renal', 'indication']`.

## Intended Purpose
It acts as a synthetic testing fixture for early orchestrator integration tests, ensuring predictable deterministic retrieval outcomes.

## Search for Authorized Baseline
A search through `src/`, `experiments/`, and `pyproject.toml` (which includes `sentence-transformers>=6.0.1`) found no concrete implementation of a production semantic baseline model in the baseline retrieval path. `CURRENT_ARCHITECTURE_SNAPSHOT.md` explicitly lists `SimpleEmbeddingModel` as the dense channel. No other authorized semantic baseline exists in the project configuration.
