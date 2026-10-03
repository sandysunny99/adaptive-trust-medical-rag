# Provider Factory Implementation

The __init__.py file was updated to integrate the sync adapter seamlessly:
1. LLMBackend Protocol was modified to specify a synchronous generate contract, explicitly reflecting the RAGOrchestrator expectation.
2. The LIVE_LLM branch in get_backend() wraps the RoutedLLMBackend in the SyncLLMBackendAdapter before returning it.
3. The DETERMINISTIC_MOCK branch continues to return the unwrapped async MockLLMBackend, preserving existing Mock tests.
