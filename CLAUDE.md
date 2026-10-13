# CLAUDE.md

Claude Code entry point. The project rules live in the files below and are imported, not copied; edit them at their source.

@AGENTS.md

## Detailed rules (from the medical-rag-security agent plugin)

@.agents/plugins/medical-rag-security/rules/medical-safety.md
@.agents/plugins/medical-rag-security/rules/security.md
@.agents/plugins/medical-rag-security/rules/privacy.md
@.agents/plugins/medical-rag-security/rules/rag-integrity.md
@.agents/plugins/medical-rag-security/rules/development.md

## Claude Code wiring

- Skills: `.claude/skills/` holds the eight domain skills ported from `.agents/plugins/medical-rag-security/skills/`. Keep both copies in sync when a skill changes. Known discrepancy: the `.agents/` copy of `medical-rag-architecture/SKILL.md` has NUL bytes in place of the leading `0` of the R0–R3 trust thresholds; the `.claude/` copy restores 0.30 / 0.45 / 0.60 / 0.75 (matching `trust_scorer.py`). Repairing the `.agents/` source is a separate follow-up.
- Third-party skills (each folder has `LICENSE` and `SOURCE.txt` with the pinned commit): `prompt-master`, `test-driven-development`, `debugging-and-error-recovery`.
- Hooks: `.claude/hooks/` adapts the existing `.agents/scripts/check_dangerous_cmd.py` and `pre_commit_secret_scan.py` gates to Claude Code (configured in `.claude/settings.json`).
- MCP: `.mcp.json` registers the local `medical-rag` server. `ingest_document` always asks for approval.
- Development memory (decisions, file paths, task state) must never contain API keys, `.env` contents, PHI or clinical source text.
