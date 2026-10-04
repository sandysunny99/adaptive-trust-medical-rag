# BASELINE READINESS AUDIT

## 1. Finding: Baseline is a Synthetic Fixture, NOT the Protocol Engine

The audit of `experiments/cognee_gate5_full_rerun.py` shows that the Baseline retrieval adapter is implemented as follows (lines 121-137):

```python
class BaseAdapterMock:
    def __init__(self, manifest):
        self.manifest = manifest
    def retrieve(self, query: str, **kwargs) -> list[ScoredCandidate]:
        results = []
        for did, chunks in self.manifest.items():
            for cid, meta in chunks.items():
                c = Candidate( ... )
                results.append(ScoredCandidate(candidate=c, rrf_score=0.9))
        return results
```

This is wrapped in `TamperingRetrievalWrapper` which does:
```python
if target_doc:
    results = [r for r in results if r.candidate.document_id == target_doc]
```

## 2. Classification

- **Baseline Type**: Synthetic Mock (`BaseAdapterMock`)
- **Retrieval Realism**: None. It returns all documents deterministically, bypassing any real vector/keyword search, and relies on target-document hardcoding from the test runner.
- **Protocol Conformance**: Fails requirement B (Both retrieval modes executed) for the authorized experimental pipeline, as the Baseline mode is not executing the actual `HybridRetrievalEngine` defined for this architecture.

## 3. Readiness Status

**`BASELINE_FULL_GATE5_READINESS = NOT_ESTABLISHED`**

Before Full Gate 5 can be considered valid, the Baseline path must use the actual `HybridRetrievalEngine` from `src/adaptive_trust_medical_rag/retrieval/hybrid_retrieval.py` against a populated evidence index, rather than a deterministic dictionary iterator.
