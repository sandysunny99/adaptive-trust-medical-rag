# Pull Request Template
# Save as: .github/PULL_REQUEST_TEMPLATE.md

## Description

Briefly describe what this PR does and why.

Closes #

---

## Type of Change

- [ ] `feat` — New feature / pipeline component
- [ ] `fix` — Bug fix
- [ ] `security` — Security hardening
- [ ] `data` — Ingestion, schema, or provenance change
- [ ] `eval` — Evaluation / experiment change
- [ ] `docs` — Documentation only
- [ ] `chore` — Config, build, or infrastructure

---

## Security Checklist

> [!CAUTION]
> All items must be checked before requesting review.

- [ ] No hardcoded API keys, passwords, tokens, or connection strings
- [ ] No real Protected Health Information (PHI/PII) in any file
- [ ] No `.venv`, `.env`, audit logs, or cache files committed
- [ ] `pre_commit_secret_scan.py` found no issues (or Gitleaks if Phase 4+)
- [ ] Bandit passed without high-severity alerts (Phase 4+)
- [ ] Semgrep passed (Phase 4+)

---

## Medical/RAG Safety Checklist

- [ ] No new pharmacological claims without evidence grounding
- [ ] No citation fabrication introduced
- [ ] Evaluation dataset leakage prevention verified (test set not touched)
- [ ] Controlled abstention behaviour is preserved (not bypassed)

---

## Testing

- [ ] Unit tests added or updated
- [ ] Existing tests pass
- [ ] Smoke set (20 cases) passes (Phase 8+)

---

## Experiment Tracking (if applicable)

- Experiment ID: `exp-`
- Dataset version: `v`
- Config hash: 
