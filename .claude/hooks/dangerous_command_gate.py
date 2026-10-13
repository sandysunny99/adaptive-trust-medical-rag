#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Bash / PowerShell): dangerous-command gate.

Reuses DENY_PATTERNS and ASK_PATTERNS from .agents/scripts/check_dangerous_cmd.py.
Deny -> blocked. Ask -> user is prompted. Otherwise normal permissions apply.
"""

from __future__ import annotations

import re

from _common import emit, load_agent_script, read_payload


def main() -> None:
    payload = read_payload()
    cmd = (payload.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        return

    gate = load_agent_script("check_dangerous_cmd")
    for pattern, label in gate.DENY_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            emit(
                "deny",
                f"BLOCKED by project dangerous-command gate: [{label}]. "
                "Run it manually in a terminal after careful review if it is intended.",
            )
            return
    for pattern, label in gate.ASK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            emit("ask", f"Project dangerous-command gate: sensitive operation [{label}].")
            return


if __name__ == "__main__":
    main()
