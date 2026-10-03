# P0 GLOBAL VS CITED SUPPORT
- **Global Support**: Measured across all session chunks (`max_ent` in `verify`).
- **Cited Support**: Measured only across `cited_chunks` (`cit_ent`).
- **Integration**: The fix securely separates these. A claim MUST pass Cited Support (`citation_supports=True`) to be assigned a passing state. Global support alone is no longer sufficient.
