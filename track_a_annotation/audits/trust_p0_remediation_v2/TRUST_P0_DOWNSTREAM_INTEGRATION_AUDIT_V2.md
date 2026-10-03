# TRUST P0 DOWNSTREAM INTEGRATION AUDIT V2

- `rag_orchestrator.py`: Receives the diluted trust score. Safely compares `float >= float`. Missing required evidence causes natural threshold failure, cleanly routing to documented controlled abstention.
- `live_variants.py`: Logs trust scores. Safely receives floats.
- `claim_verifier_v2.py`: Security behaviors unaffected.
