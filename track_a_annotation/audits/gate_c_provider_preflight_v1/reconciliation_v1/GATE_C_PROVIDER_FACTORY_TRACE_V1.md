# Provider Factory Trace

**Entry Point**: src/adaptive_trust_medical_rag/llm_backend/__init__.py::get_backend()

**Logic Flow**:
1. Evaluates LLM_MODE. If LIVE_LLM, it proceeds to load providers.
2. Extracts LLM_PRIMARY_PROVIDER (defaults to groq).
3. Instantiates backends:
   - GroqBackend
   - GoogleGeminiBackend
   - CloudflareBackend
   - HuggingFaceBackend
4. Creates LLMProviderRouter with configured backends.
5. Returns RoutedLLMBackend(router=router).

**Critical Finding**: The factory directly returns RoutedLLMBackend, which implements sync def generate(...). It does **not** wrap it in SyncLLMBackendAdapter.