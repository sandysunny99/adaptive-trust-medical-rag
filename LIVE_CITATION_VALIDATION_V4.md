# Live Citation Validation V4

## Implementation Details

1. **Mapping and Tracing:**
   In `live_application.py`, the system maps citation indexes to `EvidenceChunk` elements inside `evidence_chunk_objs`. `ClaimVerifierV2` performs NLI (Natural Language Inference) checks to determine whether the text of the claim is supported by the text of the chunk(s) it cites.

2. **Required Preconditions:**
   - Source exists.
   - Evidence chunk exists.
   - Evidence chunk was verified in the retrieved live corpus via SHA-256 validation.
   - Citation effectively maps to the evidence.
   - The verified evidence supports the claim textually.

3. **Validation Result:**
   - [x] Backend logic mapping configured.
   - [x] Supported state validation implemented.
   - [ ] Live integration test (Blocked: `PROVIDER_CONFIGURATION_REQUIRED`).
