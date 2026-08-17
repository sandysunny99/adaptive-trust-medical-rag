# Security Policy

## Non-Clinical Research Platform

This project is a **research platform** — NOT a clinical decision-making system.
See [AGENTS.md](AGENTS.md) for full operational rules.

---

## Supported Phases

| Phase | Security Coverage |
|-------|------------------|
| Phase 1–2 (current) | Regex secret scanning, dangerous command gate, `.gitignore` |
| Phase 4+ | Gitleaks, Bandit, Semgrep, Trivy, pre-commit hooks |
| Phase 8+ | Full RAG security pipeline (injection defense, poisoning defense) |

---

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

1. Email: `sandysunny99@users.noreply.github.com`  
   *(or use the GitHub private vulnerability reporting feature)*
2. Include: steps to reproduce, potential impact, suggested fix.
3. Expected response: acknowledgement within 72 hours.

---

## Security Rules (enforced by hooks and rules files)

- No PHI or real patient data — ever
- No hardcoded credentials, API keys, or tokens
- All retrieved documents are treated as untrusted data
- Abstention is a valid and expected outcome
- Pre-commit secret scanning is mandatory from Phase 4+

See [.agents/plugins/medical-rag-security/rules/security.md](.agents/plugins/medical-rag-security/rules/security.md)
