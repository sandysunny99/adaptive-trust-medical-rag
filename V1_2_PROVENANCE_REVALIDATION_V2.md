> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# V1.2 PROVENANCE REVALIDATION V2

A. Attempts 1-6 crashed before request execution. Attempt 7 executed provider calls.
B. Attempts 1-6 failed during setup/imports or early loop logic (e.g. ScoredCandidate init).
C. Only attempt 7 wrote to RUN_001.
D. Only attempt 7 touched results.jsonl (size was 0 before it).
E. Yes, attempt 7 was one uninterrupted process.
F. runner.py was loaded once per process.
G. Changes made before attempt 7 affected attempt 7, but no changes were made *during* attempt 7.
H. No code changes could have affected records after request execution began.

**Conclusion:**
CLOSED - SAME RUNNER VERSION FOR ALL 160 REQUESTS
