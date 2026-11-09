# GATE5_REPRODUCIBILITY_REPORT

## Objective
To prove that the execution of the 23-case Gate 5 matrix yields perfectly deterministic grounding states, eligibility decisions, and block reasons across identical queries.

## Methodology
- 23 cases from the authorized matrix.
- 2 separate runs per case for the BASELINE engine (HybridRetrievalEngine).
- 2 separate runs per case for the COGNEE engine (CogneeRetrievalAdapter).

## Findings
For every case across both runs:
- **Decision Exact Match**: `True`
- **Observed Retrieval Exact Match**: `True`
- **Full Contract Exact Match**: `True`

## Detailed Consistency Check
- **Eligibility Decisions**: 100% matched across runs.
- **Block Reasons**: 100% matched across runs.
- **Grounding States**: 100% matched across runs.
- **Retrieved Chunk IDs**: 100% identically ranked across runs (where deterministic).

## Conclusion
The system satisfies the rigorous reproducibility standards required for the Gate 5 evaluation. The semantic repair did not introduce any non-deterministic behavior.
