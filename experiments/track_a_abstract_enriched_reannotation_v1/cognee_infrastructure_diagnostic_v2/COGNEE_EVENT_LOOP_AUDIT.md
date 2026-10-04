# COGNEE EVENT LOOP AUDIT V2

## 1. The Problem

The orchestrator's `query()` method is **synchronous**. Cognee's `search()` is **async**. The original Gate 5 script solved this by precomputing all search results before case execution — which violated the protocol requirement for live per-case retrieval.

## 2. Architecture of the Original Gate 5 Script

```
main() [async]
  └─ await ingest_cognee()        # async — OK
  └─ for case in CASES:
       precomputed[query] = await cognee.search(...)  # async — OK, but done BEFORE cases
  └─ ThreadPoolExecutor:
       run_case()                   # sync thread
         └─ BridgedCogneeAdapter.retrieve()  # sync
              └─ self.precomputed_search.get(query, [])  # dict lookup, no async
```

The `BridgedCogneeAdapter.retrieve()` never calls `cognee.search()` — it only reads from the precomputed dict.

## 3. Why the Precomputed Approach Was Used

If `run_case()` is dispatched via `ThreadPoolExecutor`, calling `asyncio.run()` or `loop.run_until_complete()` from within a thread can fail because:
- `asyncio.run()` creates a new event loop, which may conflict with Cognee's internal event loop state
- `loop.run_until_complete()` on the main loop from a thread raises `RuntimeError: This event loop is already running`

The precomputed cache was an engineering workaround for this concurrency issue.

## 4. Correct Architecture for Live Cognee Retrieval

Option A — **Run cases sequentially in async context** (simplest):
```python
async def main():
    await ingest_cognee()
    for case in CASES:
        for mode in [True, False]:
            for run_idx in [1, 2]:
                result = await run_case_async(case, run_idx, mode, manifest, registry)
```
This avoids ThreadPoolExecutor entirely. Each `run_case_async` can call `await cognee.search()` directly.

Option B — **Use `nest_asyncio`** (if ThreadPoolExecutor is required):
```python
import nest_asyncio
nest_asyncio.apply()

class BridgedCogneeAdapter:
    def retrieve(self, query, **kwargs):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            cognee.search(query, cognee.SearchType.CHUNKS, datasets=[self.dataset_name])
        )
        return self._bridge_identity(results)
```
This allows nested event loop calls but adds a dependency.

Option C — **Dedicated thread with its own event loop**:
```python
class BridgedCogneeAdapter:
    def retrieve(self, query, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(
                cognee.search(query, cognee.SearchType.CHUNKS, datasets=[self.dataset_name])
            )
        finally:
            loop.close()
        return self._bridge_identity(results)
```

## 5. Recommendation

**Option A (sequential async)** is the safest and most transparent. It eliminates the event loop problem entirely and ensures each case executes a live `cognee.search()` call. The sequential nature is acceptable for a 23-case experiment.

## 6. What Must NOT Be Done

- Do NOT precompute all search results into a dictionary
- Do NOT catch `Exception` and replace with `[]`
- Do NOT use `ThreadPoolExecutor` for Cognee-dependent cases unless the async adapter is proven to work within threads
