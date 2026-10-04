# COGNEE EVENT LOOP AUDIT

## 1. Analysis of Event Loop Failures

The `cognee_gate5_full_rerun.py` script circumvented event loop issues by using `ThreadPoolExecutor` and passing a precomputed dictionary of search results. This was done to avoid `RuntimeError: This event loop is already running`.

However, the authorized architecture for `BridgedCogneeAdapter.retrieve()` requires calling the async `cognee.search()` at case retrieval time.

## 2. Event Loop Solution

The orchestrator's `query()` method is synchronous. If we must call `cognee.search()` (which is async) from within a synchronous orchestrator method, we cannot use `asyncio.run()` if the orchestrator itself is being run inside an already-running event loop or a thread pool that lacks a proper loop context.

The safest minimum pattern for `BridgedCogneeAdapter.retrieve()` is:

```python
import asyncio

class BridgedCogneeAdapter:
    def __init__(self, dataset_name):
        self.dataset_name = dataset_name
        
    def retrieve(self, query: str, **kwargs) -> list[ScoredCandidate]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            
        results = loop.run_until_complete(
            cognee.search(query, cognee.SearchType.CHUNKS, datasets=[self.dataset_name])
        )
        return self._bridge_identity(results)
```

By ensuring `nest_asyncio` is applied globally (or at least during initialization) and fetching the loop correctly, the adapter can execute real-time searches without rewriting the entire orchestrator to be asynchronous.

## 3. Required Action
In the next version of the Gate 5 script, the `BridgedCogneeAdapter` must implement a safe synchronous wrapper for `cognee.search()`, and the precomputed cache must be deleted.
