---
name: development-rules
description: Development environment practices, reproducible dependency management via uv, test gates, and git workflow.
trigger: always_on
---

# Development & Environment Rules

## 1. Package Management & Environment Isolation
- Use `uv` exclusively for Python package management.
- All dependencies must be specified in `pyproject.toml` and pinned in `uv.lock`.
- Never run global `pip install` commands. Run all commands within the project virtual environment (`.venv`).

## 2. Supply Chain & Code Quality Standards
- Code formatting and linting are enforced using `ruff`.
- Security testing with `bandit` and `semgrep` must pass without high-severity alerts.
- Secrets scanning with `gitleaks` is mandatory prior to pushing commits.

## 3. Evaluation & Dataset Integrity
- Evaluation datasets (smoke: 20 cases, dev: 100 cases, val: 200 cases, test: 500+ cases) must remain strictly segregated.
- The 500+ test set is frozen and never used for prompt engineering, threshold tuning, or indexing.
- Experiment runs must be tracked with full configuration hashes (model, prompt version, trust weights, retriever config).
