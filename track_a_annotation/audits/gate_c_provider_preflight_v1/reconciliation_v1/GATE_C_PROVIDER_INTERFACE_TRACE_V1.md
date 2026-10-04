# Exact Adapter Interface Trace

The following trace demonstrates the exact type mismatch preventing provider execution.

| COMPONENT | SIGNATURE | ASYNC? | RETURN TYPE | CONSUMER | COMPATIBLE? | EVIDENCE |
|-----------|-----------|--------|-------------|----------|-------------|----------|
| RAGOrchestrator | generate(prompt: str) -> str | NO | str | N/A | N/A | 
ag_orchestrator.py:377 |
| LLMBackend (Expected) | generate(prompt: str) -> str | NO | str | RAGOrchestrator | YES | 
ag_orchestrator.py:103 |
| RoutedLLMBackend | sync def generate(prompt: str) -> Any | YES | ModelGenerationResult | RAGOrchestrator | **NO** | 
outed_llm_backend.py:24 |
| SyncLLMBackendAdapter | generate(prompt: str) -> str | NO | str | None (Unused) | YES | sync_adapter.py:33 |
| GroqBackend | sync def generate(prompt: str) -> ModelGenerationResult | YES | ModelGenerationResult | RoutedLLMBackend | YES | groq_backend.py:27 |
| CloudflareBackend | sync def generate(prompt: str) -> ModelGenerationResult | YES | ModelGenerationResult | RoutedLLMBackend | YES | cloudflare_backend.py:38 |
| HuggingFaceBackend | sync def generate(prompt: str) -> ModelGenerationResult | YES | ModelGenerationResult | RoutedLLMBackend | YES | huggingface_backend.py:30 |

### Conclusion
RAGOrchestrator receives RoutedLLMBackend from the factory. When it calls .generate(prompt), it receives a Python coroutine instead of a string, causing an immediate runtime failure. SyncLLMBackendAdapter is designed to bridge this but is currently IMPLEMENTED_NOT_CONNECTED.