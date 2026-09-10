# Phase 14.7 — LLM Resilience Layer Architecture

## Design Principle: Routing Plane / Security Plane Separation

```
APPLICATION
│
┌─────────┴─────────┐
│                   │
ROUTING PLANE       SECURITY PLANE
│                   │
retry/failover      PromptInjectionDetector
circuit breaker     RetrievalPoisoningDetector
provider health     AdaptiveTrustScorer
rate-limit          SourceValidator
quota telemetry     EvidenceEligibility
                    ClaimVerifier
▼                   ContradictionAnalysis
LLM                 ControlledAbstention
│                   AuthorizationBoundary
│                   ToolExecutor
└─────────┬─────────┘
          ▼
      AUDIT PLANE
```

The ROUTING PLANE handles only provider availability and transport.
The SECURITY PLANE handles all medical/security/trust decisions.
These two planes are architecturally independent.

## Component Architecture

```
RAG Orchestrator
    ↓
RoutedLLMBackend (satisfies LLMBackend protocol: generate(str) -> str)
    ↓
LLMProviderRouter
    ├── RetryPolicy (bounded exponential backoff + jitter)
    ├── CircuitBreaker (per provider: CLOSED/OPEN/HALF_OPEN)
    ├── ProviderHealthRegistry (latency, failures, quota, circuit state)
    └── ProviderConfig (priority-ordered provider list)
        ├── GeminiBackend (primary)
        ├── GroqBackend (secondary)
        └── LocalBackend (optional tertiary)
```

## Provider Execution Flow

```
PRIMARY PROVIDER
    ↓
  attempt 1  ──→  success  ──→  return ProviderAttemptResult
    ↓ (transient failure)
  attempt 2  ──→  success  ──→  return ProviderAttemptResult
    ↓ (transient failure)
  attempt 3  ──→  success  ──→  return ProviderAttemptResult
    ↓ (retry exhausted)
Circuit Breaker evaluation
    ↓
SECONDARY PROVIDER
    ↓
  attempt 1  ──→  success  ──→  return ProviderAttemptResult
    ↓ (transient failure)
  attempt 2 ...
    ↓ (retry exhausted)
TERTIARY PROVIDER / LOCAL
    ↓ (all exhausted)
AllProvidersUnavailableError
    ↓
CONTROLLED ABSTENTION (LLM_PROVIDER_UNAVAILABLE)
```

## Non-Retryable / Non-Failover Errors

The following errors are NEVER retried and NEVER trigger failover:

- 401 Authentication failure
- 403 Authorization failure
- 400 Invalid request
- Invalid model ID
- Schema/structured output failure
- Security BLOCK
- Authorization denial
- Evidence rejection
- Claim verification failure

These represent application-level or security-level decisions, not provider availability problems.

## Scientific Mode

In `SCIENTIFIC` mode:
- Failover is DISABLED
- The intended provider/model is frozen at experiment initialization
- Every call validates: `actual_provider == expected_provider`
- Provider mismatch → `ExperimentProviderUnavailable` (never silently substituted)
- The scientific runner decides observation validity

## Security Invariants

Provider failover MUST NOT bypass:
1. PromptInjectionDetector
2. RetrievalPoisoningDetector
3. AdaptiveTrustScorer
4. SourceValidator
5. EvidenceEligibilityGate
6. ClaimVerifier
7. ContradictionAnalysis
8. ControlledAbstention
9. AuthorizationBoundary
10. ToolExecutor

A provider change must NEVER produce ALLOW because a previous provider failed.
