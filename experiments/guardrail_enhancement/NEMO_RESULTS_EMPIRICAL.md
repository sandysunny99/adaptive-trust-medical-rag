# NEMO RESULTS (Study A2)

## Dependency Control
- **Package:** `nemoguardrails`
- **Pinned Version:** `0.9.1.1`
- **Python Compatibility:** Python 3.9 - 3.11
- **Security & Dependency Findings:** 
  - **CRITICAL:** Installation requires Microsoft Visual C++ 14.0 or greater (to build the `annoy==1.17.3` dependency wheel).
  - In our standard Windows development environment, `uv add nemoguardrails` failed catastrophically during the build backend compilation.
  - Adding this dependency imposes a severe constraint on the host machine (requiring a full C++ build toolchain) which breaks portability and maintainability.

## Summary
- **Execution Date:** 2026-09-13
- **Status:** NOT EXECUTED / FAILED INSTALLATION
- **Dataset:** 120-case Dev Benchmark

## Empirical Results
- Because `nemoguardrails` failed to install in the tightly controlled development environment, no empirical metrics (TP/TN, latency, LLM calls) could be gathered.

## Conclusion
NeMo Guardrails introduces an unacceptable dependency burden (`annoy` C++ build requirements) that prevents seamless cross-platform installation. Due to the installation failure, it is marked as `NOT_EXECUTED` and cannot be selected as the primary security layer.
