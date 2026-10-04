# RESEARCH GAPS

- **Claim-Level Relationship Checking**: Current state-of-the-art medical RAG relies heavily on NLI, but NLI cannot reliably enforce structural relationships (e.g. Drug A interacts with Drug B vs Drug B interacts with Drug A). A structural relationship extractor for claims is required for E2E clinical safety.
- **Missing Data Semantics for Claims**: The trust scorer correctly implements missing data semantics, but this ontology does not yet map clearly to generated claim confidence.
