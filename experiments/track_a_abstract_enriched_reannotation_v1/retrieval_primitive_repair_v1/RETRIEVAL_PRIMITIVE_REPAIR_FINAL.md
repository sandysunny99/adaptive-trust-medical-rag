# Retrieval Primitive Status: BASELINE_MODEL_NOT_AUTHORIZED

## Conclusion
1. **BM25 False Positive**: The previous report of a "missing accumulation bug" was a false positive. BM25 is mathematically and implementation-wise correct. A true runtime execution captures scores and ranks documents as expected.
2. **Provenance of SimpleEmbeddingModel**: `SimpleEmbeddingModel` is a temporary test fixture (7-word vocabulary) introduced to enable end-to-end execution testing. It is *not* the authorized experimental baseline embedding model. It was accidentally captured in `CURRENT_ARCHITECTURE_SNAPSHOT.md`.
3. **Live Retrievals Checked**: 
   - Cognee was able to execute `add -> cognify -> search` live, capturing native responses (although semantic search matched nothing due to vocabulary limits).
   - The current baseline pipeline correctly routes BM25, Dense, and Graph queries to the RRF fusion engine. RRF correctly functions on available candidates. 
   - Differences in retrieved candidates confirm that outputs are indeed query-driven.
4. **Current Status**: The authorized experimental baseline is missing a proper semantic embedding model (e.g. `sentence-transformers` based, as suggested by `pyproject.toml`).

## Final Answers
**"According to the authoritative research protocol, what exact embedding implementation is the baseline supposed to use?"**
Unspecified. The protocol failed to declare a production baseline model, and the implementation fell back on a 7-word testing mock (`SimpleEmbeddingModel`). This mock is not authorized.

**"Do we have independently captured runtime evidence that the current retrieval pipeline returns the actual Gate 5 candidates?"**
Yes, we now have real execution traces. However, because the semantic channel mock cannot match standard vocabulary, the current candidates rely almost entirely on BM25. The actual candidate set is not semantically realistic for Gate 5.

Therefore: **FULL GATE 5 STOPPED** / **Gate 6 NOT AUTHORIZED**.
The experimental baseline model authorization must be resolved first.
