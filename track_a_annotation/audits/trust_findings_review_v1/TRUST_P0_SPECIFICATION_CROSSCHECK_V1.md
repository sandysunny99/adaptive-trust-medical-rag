# TRUST P0 SPECIFICATION CROSS-CHECK V1

**Status**: CODE_SPECIFICATION_MISMATCH

A review of project specifications (`medical-safety.md`, `rag-integrity.md`, and `AGENTS.md`) shows explicit rules for handling trust thresholds (e.g., "Abstain if trust < threshold"), but NO specification defining that missing trust data should be silently defaulted to 0.0 or 1.0. 
Silent imputation bypassing uncertainty representation violates the spirit of the evidence-grounded research requirements.
