# TRACK_A_LLM_REAL_ADAPTER_INTEGRATION_TEST_V1

| Test | Execution path | Input condition | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| RELEVANT + grade 2 -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| RELEVANT + grade 1 -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | PASS |
| PARTIALLY_RELEVANT + grade 1 -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| PARTIALLY_RELEVANT + grade 2 -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | PASS |
| IRRELEVANT + grade 0 -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| IRRELEVANT + grade 1 -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | PASS |
| INSUFFICIENT_INFORMATION + grade 0 -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| INSUFFICIENT_INFORMATION + grade 2 -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | PASS |
| AMBIGUOUS + null -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| AMBIGUOUS + 0 -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | SEMANTIC_SCHEMA_CONSISTENCY_FAILED | PASS |
| best_supporting_span exact substring -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| paraphrased span -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| invented span -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| IRRELEVANT + empty best_supporting_span -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| INSUFFICIENT_INFORMATION + empty -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| AMBIGUOUS + empty -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| RELEVANT + empty -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| PARTIALLY_RELEVANT + empty -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| exact span -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| paraphrased span -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| invented span -> REJECT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SPAN_VALIDATION_FAILED | SPAN_VALIDATION_FAILED | PASS |
| multiple valid spans -> ACCEPT | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| alternative_label_considered valid (RELEVANT) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| alternative_label_considered valid (null) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SUCCESS | SUCCESS | PASS |
| alternative_label_considered invalid (UNKNOWN) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SCHEMA_VALIDATION_FAILED | SCHEMA_VALIDATION_FAILED | PASS |
| alternative_label_considered invalid (LIKELY) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SCHEMA_VALIDATION_FAILED | SCHEMA_VALIDATION_FAILED | PASS |
| alternative_label_considered invalid (2) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SCHEMA_VALIDATION_FAILED | SCHEMA_VALIDATION_FAILED | PASS |
| alternative_label_considered invalid (maybe) | LLMProviderAdapter.generate_structured() | Mocked JSON returning specified payload | SCHEMA_VALIDATION_FAILED | SCHEMA_VALIDATION_FAILED | PASS |
