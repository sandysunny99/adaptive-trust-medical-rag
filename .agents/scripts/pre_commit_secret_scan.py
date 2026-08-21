#!/usr/bin/env python3
"""
Secret Detection Gate — PreToolUse Hook (file write events)
Project: Adaptive Trust-Aware Medical RAG

Runs lightweight regex-based secret scanning on file content
before it is written to disk.

Phase 4+: When Gitleaks v8.30.1 is installed, this script will
additionally invoke `gitleaks detect` for comprehensive scanning.
Until then, the regex layer provides a first line of defence.

Output: {"decision": "allow"} or {"decision": "deny", "reason": "..."}
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Regex patterns for obvious secrets
# These catch hard-coded values — not environment variable references.
# ──────────────────────────────────────────────────────────────
SECRET_PATTERNS = [
    # Generic assignment patterns
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\'${\s]{6,}["\']', "Hardcoded password"),
    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][A-Za-z0-9_\-]{16,}["\']', "Hardcoded API key"),
    (r'(?i)(secret|token|auth)\s*=\s*["\'][A-Za-z0-9_\-]{16,}["\']', "Hardcoded secret/token"),
    # Well-known token formats
    (r"ghp_[A-Za-z0-9]{36,}", "GitHub PAT (ghp_)"),
    (r"ghs_[A-Za-z0-9]{36,}", "GitHub App token (ghs_)"),
    (r"github_pat_[A-Za-z0-9_]{82}", "GitHub fine-grained PAT"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI-style secret key (sk-)"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API key (AIza)"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY", "Private key block"),
    # Connection strings with embedded credentials
    (r"(?i)postgres(?:ql)?://[^:@\s]+:[^@\s]{4,}@", "PostgreSQL DSN with credentials"),
    (r"(?i)mysql://[^:@\s]+:[^@\s]{4,}@", "MySQL DSN with credentials"),
    (r"(?i)mongodb(\+srv)?://[^:@\s]+:[^@\s]{4,}@", "MongoDB DSN with credentials"),
    (r"(?i)redis://:([^@\s]{4,})@", "Redis DSN with credentials"),
    (r"(?i)amqp://[^:@\s]+:[^@\s]{4,}@", "AMQP DSN with credentials"),
]

# Paths that are exempt from scanning (test fixtures with SYNTHETIC data)
EXEMPT_PATH_PATTERNS = [
    r"evaluation[/\\]",
    r"tests[/\\]",                    # all test files - synthetic mock data
    r"\.agents[/\\]scripts[/\\]",  # hook scripts - contain secret regex patterns
    r"\.gitleaks\.toml$",             # gitleaks config - not actual secrets
    r"\.env\.example$",
    r"\.env\.template$",
]

# Patterns that indicate the value is a variable reference, not a literal secret
SAFE_VALUE_PATTERNS = [
    r"\$\{[A-Z_]+\}",  # ${ENV_VAR}
    r"\$[A-Z_]+\b",  # $ENV_VAR
    r"os\.environ",  # os.environ["KEY"]
    r"os\.getenv",  # os.getenv("KEY")
    r"settings\.",  # settings.secret
    r"config\.",  # config.secret
    r"<[A-Z_]+>",  # <PLACEHOLDER>
    r"YOUR_.*HERE",  # YOUR_KEY_HERE
    r"REPLACE_ME",
    r"example\.",
    r"test_secret",
    r"fake_",
    r"dummy_",
    r"mock_",
]


def is_exempt_path(path: str) -> bool:
    for pattern in EXEMPT_PATH_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False


def is_safe_value(content_snippet: str) -> bool:
    for pattern in SAFE_VALUE_PATTERNS:
        if re.search(pattern, content_snippet, re.IGNORECASE):
            return True
    return False


def scan_with_regex(content: str) -> list[str]:
    findings = []
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        for pattern, label in SECRET_PATTERNS:
            match = re.search(pattern, line)
            if match:
                # Check if the matched line looks like a safe reference
                if not is_safe_value(line):
                    findings.append(f"{label} (line {i})")
    return findings


def scan_with_gitleaks(content: str) -> list[str]:
    """Run Gitleaks on the content if available (Phase 4+)."""
    import os

    gitleaks_bin = shutil.which("gitleaks")
    if not gitleaks_bin:
        return []  # Gitleaks not installed — skip

    # In CI environments the gitleaks binary is installed globally for repo
    # scanning, not for inline content scanning. Skip to avoid false positives
    # caused by gitleaks scanning temp files without project context.
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return []

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "content_scan.txt"
            tmp_file.write_text(content, encoding="utf-8")
            # Locate project .gitleaks.toml for consistent rule application
            config_args: list[str] = []
            workspace_root = Path(__file__).resolve().parent.parent.parent
            project_config = workspace_root / ".gitleaks.toml"
            if project_config.exists():
                config_args = ["--config", str(project_config)]
            result = subprocess.run(  # nosec B603
                [
                    gitleaks_bin, "detect",
                    "--source", str(tmp_dir),
                    "--no-git", "--quiet",
                    *config_args,
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
        if result.returncode != 0:
            return ["Gitleaks detected secrets — run `gitleaks detect` for details"]
        return []
    except Exception:
        return []  # Gitleaks scan failed — don't block on tool errors


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.stdout.write(json.dumps({"decision": "allow"}))
        return

    args = data.get("toolCall", {}).get("args", {}) or data.get("args", {}) or data

    # Extract target file path for exemption check
    target_file = args.get("TargetFile", "") or args.get("AbsolutePath", "") or ""
    if target_file and is_exempt_path(target_file):
        sys.stdout.write(json.dumps({"decision": "allow"}))
        return

    # Extract content from any file-write tool
    content = args.get("CodeContent", "") or args.get("ReplacementContent", "") or ""
    if not content or not isinstance(content, str):
        sys.stdout.write(json.dumps({"decision": "allow"}))
        return

    # Run regex scan
    regex_findings = scan_with_regex(content)

    # Run Gitleaks scan if available
    gitleaks_findings = scan_with_gitleaks(content)

    all_findings = regex_findings + gitleaks_findings

    if all_findings:
        unique = list(dict.fromkeys(all_findings))  # Deduplicate, preserve order
        sys.stdout.write(
            json.dumps(
                {
                    "decision": "deny",
                    "reason": (
                        f"SECRET DETECTED — file write blocked. "
                        f"Findings: {'; '.join(unique)}. "
                        "Use environment variables instead of hardcoded credentials. "
                        "See AGENTS.md security rules. The file has NOT been written."
                    ),
                }
            )
        )
        return

    sys.stdout.write(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
