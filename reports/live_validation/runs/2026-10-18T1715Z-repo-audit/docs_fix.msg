docs: restore the README and architecture sections the doc tests require

tests/test_docs.py checks for the research-question, safety-gate, threat-model, setup, CLI,
REST API, ablation, scorecard and license sections in README.md and for the eligibility gate,
answer gate, authority, freshness, trust calculation, database schema, threat model and
research integrity topics in docs/ARCHITECTURE.md. Add them with current content: the CLI
examples use the parser's real syntax, the scorecard section states that no empirical
scorecard exists yet (the A-F tables are simulation output), and the trust section documents
the nine factors and per-tier weights from config/trust.yaml and the stored per-chunk
authority and freshness values.

Documentation only.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
