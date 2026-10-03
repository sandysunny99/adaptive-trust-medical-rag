# SERIALIZATION REGRESSION
- `EvidenceChunk` and `SemanticJudgment` natively serialize via standard dataclass functions.
- Local tests confirm dict/json serialization preserves all augmented metadata fields.
