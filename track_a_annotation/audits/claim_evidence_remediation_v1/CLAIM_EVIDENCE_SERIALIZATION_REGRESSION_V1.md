# SERIALIZATION REGRESSION
Dataclasses (`EvidenceChunk`, `SemanticJudgment`) were augmented natively. Standard `dataclasses.asdict` serializes the new fields flawlessly without custom encoder changes.
