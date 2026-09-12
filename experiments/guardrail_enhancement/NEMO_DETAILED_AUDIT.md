# NVIDIA NeMo Guardrails Audit (Part 3)

## Version & Dependencies
- **License**: Apache 2.0
- **Maintenance**: Active (NVIDIA)
- **Dependency Footprint**: Very large (requires LangChain, PyYAML, nest-asyncio, typing-extensions, etc.)

## Rail Mapping to Custom Architecture
| Rail Type | Custom Module | Fit | Note |
|---|---|---|---|
| Input Rails | PromptInjectionDetector | High | Can replace or augment basic regex with semantic intent detection. |
| Retrieval Rails | RetrievalPoisoningDetector | Low | Custom logic relies on specific SHA-256 corpus manifest validation. NeMo retrieval rails would require heavy customization. |
| Execution Rails | AuthorizationBoundary | Low | NeMo's execution rails expect to own the action loop. We must enforce AgentActionRequest -> AuthorizationBoundary. |
| Output Rails | ClaimVerifier, AnswerSafetyGate | Medium | NeMo can enforce factual consistency, but our custom NLI contradiction detection is specialized. |

## LLM Inference Implications
NeMo relies heavily on the LLM to evaluate rails via specialized prompts (e.g., self-checking input/output).
- **Extra LLM Calls**: High. Typical NeMo flows add 1-3 extra LLM calls per interaction.
- **Latency**: Will significantly increase due to sequential LLM guardrail calls.

## Conclusion
NeMo is best used as a DEFENSE-IN-DEPTH layer (specifically Input Rails) but should NOT replace the core Trust Engine or Authorization Boundary.
