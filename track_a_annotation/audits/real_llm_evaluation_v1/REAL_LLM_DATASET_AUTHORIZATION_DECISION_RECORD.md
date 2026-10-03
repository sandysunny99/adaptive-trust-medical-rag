# Real-LLM Dataset Authorization Decision Record

## Proposed Dataset
- **Dataset Path**: experiments/manifests/v3_1_human_cases.json
- **Dataset Hash**: db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc
- **Case Count**: 80
- **Case IDs Hash**: bb47d3c18a0c9bf5488437bc0bca873c4cd5ee4a2d6c7f8ce133ac6cd505da2f

## Authorization Context
- **Intended Use**: Real-LLM medical generation evaluation (Real-LLM Protocol V1).
- **Original Use**: Information Retrieval (IR) benchmarking and evidence span labeling (v3.1 Annotation Guide).
- **Known Limitations**: Lacks generative answer-level ground truth; abstention expectations must be inferred or formally labeled.

## Decision Required
- **Status**: PENDING_RESEARCHER_DECISION
- **Basis**: There is no authoritative document in the repository formally migrating this dataset from retrieval benchmarking to real-LLM generation evaluation.

**Action Required**: A researcher must explicitly authorize this dataset or provide an alternative authorized manifest before any LLM medical execution can proceed.
