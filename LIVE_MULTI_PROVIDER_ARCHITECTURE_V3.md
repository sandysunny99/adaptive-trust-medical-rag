# Live Multi-Provider Architecture V3

## Routing Strategy
The system employs a strict failover boundary that separates infrastructure errors (transport) from medical errors (safety).

1. **Request** ? **Groq**
2. If Transport Error (429/503/Timeout) ? **NVIDIA**
3. If Transport Error (429/503/Timeout) ? **Cloudflare**
4. If Transport Error (429/503/Timeout) ? **Terminal ModelExecutionError**

If any provider raises a FailureClass.MEDICAL_SAFETY (e.g. Evidence Insufficient, Safety Gate Reject), execution **STOPS** immediately. The safety rejection is correctly propagated to the user.
