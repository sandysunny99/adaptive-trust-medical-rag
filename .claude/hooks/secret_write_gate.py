#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Write / Edit / MultiEdit / NotebookEdit): secret gate.

Reuses the regex + Gitleaks scan and path exemptions from
.agents/scripts/pre_commit_secret_scan.py. Denies the write when a secret is found.
"""

from __future__ import annotations

from pathlib import Path

from _common import PROJECT_ROOT, emit, load_agent_script, read_payload


def _relative(path: str) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except (ValueError, OSError):
        return path.replace("\\", "/")


def _new_content(tool_input: dict) -> str:
    parts = [
        tool_input.get("content"),
        tool_input.get("new_string"),
        tool_input.get("new_source"),
    ]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(p for p in parts if isinstance(p, str) and p)


def main() -> None:
    payload = read_payload()
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""

    scanner = load_agent_script("pre_commit_secret_scan")
    if target and scanner.is_exempt_path(_relative(target)):
        return
    content = _new_content(tool_input)
    if not content:
        return

    findings = scanner.scan_with_regex(content) + scanner.scan_with_gitleaks(content)
    if findings:
        unique = "; ".join(dict.fromkeys(findings))
        emit(
            "deny",
            f"SECRET DETECTED by project secret gate, write blocked. Findings: {unique}. "
            "Use environment variables instead of hard-coded credentials (AGENTS.md section 3).",
        )


if __name__ == "__main__":
    main()
