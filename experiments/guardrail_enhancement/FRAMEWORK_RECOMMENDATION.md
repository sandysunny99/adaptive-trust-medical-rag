# FRAMEWORK COMPARISON & RECOMMENDATION (Study A6)

## Scientific Benchmark Status
**CRITICAL SCIENTIFIC CORRECTION:** Within the evaluated development environment, A1_CUSTOM is currently the only guardrail implementation with a successfully executed empirical benchmark. A2 and A3 were not successfully benchmarked because of environment/integration failures. Therefore, no comparative guardrail effectiveness winner has been scientifically established.

## Decision Matrix

### CUSTOM (A1):
- **empirically executed** = YES
- **effectiveness measured** = YES
- **comparative winner** = NO

### NEMO (A2):
- **empirically executed** = NO
- **execution failure** = YES
- **effectiveness measured** = NO
- **comparative winner** = NO

### GUARDRAILS_AI (A3):
- **empirically executed** = NO
- **execution failure** = YES
- **effectiveness measured** = NO
- **comparative winner** = NO

## Engineering Selection

**ENGINEERING_SELECTION_STATUS = CUSTOM_CORE_PREFERRED_PROVISIONALLY**

This is an architectural engineering preference, not a scientific benchmark winner. It is based on:
1. Successful integration and execution in the current restricted Windows environment.
2. Existing custom security control ownership and determinism.
3. Current absence of external framework benchmark evidence due to integration/dependency failures.
4. The need to preserve the medical authorization/security boundary without introducing blocking unresolvable dependencies or unwanted default outbound telemetry.
