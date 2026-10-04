# Free Replication V1 - Scheduling and Quota Management

## 1. Quota-Aware Scheduler
The replication runner must strictly obey provider-supplied telemetry rather than using naive exponential backoff. 

**Required Telemetry Headers (Groq):**
*   `x-ratelimit-limit-requests`
*   `x-ratelimit-limit-tokens`
*   `x-ratelimit-remaining-requests`
*   `x-ratelimit-remaining-tokens`
*   `x-ratelimit-reset-requests`
*   `x-ratelimit-reset-tokens`
*   `retry-after` (If returned on 429)

**Scheduler Behavior:**
1.  After every response, parse the `remaining-tokens` and `reset-tokens` headers.
2.  If `remaining-tokens` is lower than the expected next request size (~4,000 tokens), the scheduler MUST sleep for `reset-tokens` seconds (plus a 2-second safety buffer).
3.  If a `429` error occurs, read `retry-after`. If absent, read `x-ratelimit-reset-tokens` and sleep. Do NOT exponentially backoff arbitrarily.

## 2. Daily Token Budget (TPD Margin)
*   **Documented Limit:** 200,000 TPD (Tokens Per Day).
*   **Daily Target/Safety Budget:** 180,000 TPD.
*   The scheduler maintains a cumulative daily token counter based on `attempted_tokens`. If `attempted_tokens` > 180,000 in a given rolling window, the runner MUST sleep until the next daily quota window resets.

## 3. Resource Accounting Separation
All resource usage is split to ensure scientific dataset accuracy without losing cost/quota tracking.
*   **Attempted Resources (`attempted_tokens`, `attempted_requests`):** All provider API usage, including interrupted/failed attempts. Used for strict quota and cost scheduling against API limits.
*   **Committed Resources (`committed_tokens`, `committed_requests`):** Only usage belonging to fully completed, scientifically valid benchmark pairs. Used for experimental efficiency reporting.

## 4. Checkpoint, Recovery, and Transactional Pair Commits
Because the replication will span multiple days/quota windows, **persistent, crash-resistant checkpointing is mandatory**.

*   **Pair Commit Atomicity:** To guarantee that every completed case has exactly one active baseline and one active hardened observation, observations are NOT written as independent lines as soon as they finish. Instead, the runner prepares the complete pair record in memory and atomically appends/flushes it as a single JSON transaction.
*   **Checkpoint State:** Saved to `checkpoint_free_rep_v1.json` after every API call. Records `attempted_tokens`, `committed_tokens`, etc.
*   **Resume Behavior:** Upon startup, the runner loads the checkpoint. It skips all fully paired `completed_case_ids`.
*   **Pair Integrity Rule:** If a case was interrupted (e.g., baseline complete, hardened incomplete), the incomplete pair state is discarded. The entire case is restarted from baseline. The abandoned baseline attempt remains counted in `attempted_tokens` but does NOT enter the scientific observation dataset.

## 5. Retry Taxonomy
**Retryable (Trigger Scheduler Sleep/Backoff):**
*   `429 Rate Limit` (Use header telemetry)
*   `500 / 502 / 503 / 504` (Transient server errors)
*   Recoverable network timeouts

**NOT Automatically Retryable (Trigger Case Failure):**
*   `401 / 403` (Authentication/Authorization)
*   `400` (Invalid Request / Context Too Large)
*   Model unavailable
*   Persistent schema incompatibility
*   Security/protocol violations
