# Adapter Compatibility

**LLMBackend Protocol:** generate(prompt: str) -> str
**RoutedLLMBackend:** sync def generate(prompt: str) -> ModelGenerationResult

**Result:** INCOMPATIBLE.
The orchestrator cannot directly await the async router nor process ModelGenerationResult natively without SyncLLMBackendAdapter, which is currently untracked and unintegrated in the provider factory.