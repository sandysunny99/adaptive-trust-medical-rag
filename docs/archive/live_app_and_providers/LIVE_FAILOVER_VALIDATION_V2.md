> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# Live Failover Validation

## Objective
Verify that the `LiveProviderRouter` properly implements provider fallback behavior.

## Methodology
The test suite `tests/test_router_failover_logic.py` uses mock adapters injected into the router. The mocks are programmed to raise specific `ModelExecutionError` instances with controlled `FailureClass` properties.

## Test Cases Executed

### 1. Primary Success
- **Scenario**: Primary provider (Groq) responds normally with 200 OK.
- **Result**: **PASS**. Response returned immediately. Secondary provider is not invoked.

### 2. Primary 429 → Secondary Success
- **Scenario**: Primary provider raises an error classified as `FailureClass.RATE_LIMIT` (e.g., HTTP 429).
- **Result**: **PASS**. The router logs the transport failure and gracefully retries with the secondary provider. The secondary provider returns a success, which is passed up the stack.

### 3. Primary Timeout → Secondary Success
- **Scenario**: Primary provider raises `FailureClass.TIMEOUT`.
- **Result**: **PASS**. The router correctly identifies this as a transport failure and falls back.

### 4. Primary Unknown Error → No Failover
- **Scenario**: Primary provider raises a non-transport error or a logical safety error (e.g., `Evidence insufficient`).
- **Result**: **PASS**. The router correctly propagates the error upward and does **NOT** attempt failover. Medical safety outcomes are respected.

### 5. All Providers Unavailable
- **Scenario**: Primary fails with 429, secondary fails with 503.
- **Result**: **PASS**. The router exhausts its provider list and raises a final `ModelExecutionError` containing the last failure class.

## Real vs Mock Distinction
- **MOCK VERIFIED**: All combinations of failure classes and failovers were exhaustively tested using deterministic unit tests.
- **REAL FAILOVER**: The application does not intentionally spam Groq or NVIDIA to induce real 429s during CI testing, as this consumes rate limits and violates API terms. 

## Conclusion
The failover behavior is functionally correct and properly isolated from logical safety failures.
