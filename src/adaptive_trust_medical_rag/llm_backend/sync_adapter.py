from __future__ import annotations
import asyncio
import threading
from typing import Protocol, Any
from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult

class AsyncLLMBackend(Protocol):
    async def generate(self, prompt: str) -> ModelGenerationResult:
        ...

def _run_async(coro):
    """Run an async coroutine in a new thread to avoid loop conflicts."""
    result = None
    exception = None

    def _worker():
        nonlocal result, exception
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro)
        except Exception as e:
            exception = e
        finally:
            loop.close()

    thread = threading.Thread(target=_worker)
    thread.start()
    thread.join()

    if exception is not None:
        raise exception
    return result

class SyncLLMBackendAdapter:
    """
    Synchronous wrapper for an async LLM backend.
    Adapts an async backend returning ModelGenerationResult into a sync backend returning str.
    This resolves the interface mismatch for AdaptiveTrustRAGOrchestrator which expects synchronous str generation.
    """
    def __init__(self, async_backend: AsyncLLMBackend) -> None:
        self.async_backend = async_backend
        self.last_result: ModelGenerationResult | None = None

    def generate(self, prompt: str) -> str:
        # Run asynchronously in a thread to safely await the result
        result = _run_async(self.async_backend.generate(prompt))
        self.last_result = result
        return result.response_text
