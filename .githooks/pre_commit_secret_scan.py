#!/usr/bin/env python3
"""Git pre-commit secret scan for staged changes.

1. Regex scan (from .agents/scripts/pre_commit_secret_scan.py) over the lines
   added in the staged diff, honouring that scanner's path exemptions.
2. `gitleaks git --staged` with the repo's .gitleaks.toml over everything staged,
   with no path exemptions beyond the gitleaks allowlist.

Exit 1 blocks the commit. Bypass only after manual review: `git commit --no-verify`.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_scanner():
    path = ROOT / ".agents" / "scripts" / "pre_commit_secret_scan.py"
    spec = importlib.util.spec_from_file_location("agents_secret_scan", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def staged_added_lines() -> dict[str, list[str]]:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--unified=0", "--no-color", "--diff-filter=ACMR"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    ).stdout
    added: dict[str, list[str]] = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif current and line.startswith("+") and not line.startswith("+++"):
            added.setdefault(current, []).append(line[1:])
    return added


def regex_findings(scanner) -> list[str]:
    findings = []
    for path, lines in staged_added_lines().items():
        if scanner.is_exempt_path(path):
            continue
        for finding in scanner.scan_with_regex("\n".join(lines)):
            findings.append(f"{path}: {finding} (line numbers are within the added lines)")
    return findings


def gitleaks_findings() -> list[str]:
    gitleaks = shutil.which("gitleaks")
    if not gitleaks:
        print("pre-commit: gitleaks not found, running regex scan only", file=sys.stderr)
        return []
    cmd = [gitleaks, "git", "--staged", "--no-banner", "--no-color", "--redact", "--verbose", "--exit-code", "1"]
    config = ROOT / ".gitleaks.toml"
    if config.exists():
        cmd += ["--config", str(config)]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 1:
        return ["gitleaks found secrets in staged changes:\n" + (result.stdout + result.stderr).strip()]
    if result.returncode != 0:
        print(f"pre-commit: gitleaks error (exit {result.returncode}), not blocking:\n{result.stderr.strip()}", file=sys.stderr)
    return []


def main() -> int:
    findings = regex_findings(load_scanner()) + gitleaks_findings()
    if findings:
        print("SECRET SCAN FAILED, commit blocked:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print("Use environment variables instead of hard-coded credentials (AGENTS.md section 3).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
