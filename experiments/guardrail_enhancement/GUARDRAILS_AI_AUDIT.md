# Guardrails AI Audit (Part 4)

## Version & Dependencies
- **License**: Apache 2.0
- **Dependency Footprint**: Medium

## Rail Mapping to Custom Architecture
| Capability | Custom Module | Overlap | Decision |
|---|---|---|---|
| Schema Validation | None natively (Pydantic used) | Low | **DEFENSE-IN-DEPTH**. Excellent for enforcing AgentActionRequest schema. |
| Response Validation | ClaimVerifier | High | **KEEP CUSTOM**. Guardrails AI factual consistency validators duplicate our NLI contradiction detection but with less medical specificity. |

## Conclusion
Guardrails AI excels at structured output enforcement. It should be evaluated specifically for enforcing the RAGResponse and AgentActionRequest schemas to prevent malformed tool calls.
