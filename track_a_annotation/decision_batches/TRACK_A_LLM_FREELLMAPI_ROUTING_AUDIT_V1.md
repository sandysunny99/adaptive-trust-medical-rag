# TRACK_A_LLM_FREELLMAPI_ROUTING_AUDIT_V1

## FreeLLMAPI Provenance Tracking
FreeLLMAPI is integrated as a valid GATEWAY, completely distinct from the underlying PROVIDER. The adapter natively traps routing variables to ensure the dataset isn't corrupted by silent failovers:
* **
esolved_provider**: Actively parsed from X-Routed-Via response headers (per documentation) rather than presumed custom headers.
* **allback_attempts**: Parsed from X-Fallback-Attempts.
* **
outing_changed**: Actively flipped to True if a fallback attempt occurred or if the provider could not be explicitly confirmed.

This ensures any automated routing decisions made by the gateway are recorded in the final semantic payload to maintain strict evaluation reproducibility.
