#!/usr/bin/env python3
"""
Dangerous Command Gate — PreToolUse Hook
Project: Adaptive Trust-Aware Medical RAG

Reads tool call JSON from stdin.
Outputs allow / ask / deny decision JSON to stdout.

Deny:  Clearly destructive commands — blocked outright.
Ask:   Sensitive but potentially valid commands — routed to human review.
Allow: All other commands pass through.

This hook runs SYNCHRONOUSLY before every run_command tool call.
Keep it fast: target < 500ms. No external calls.
"""

import json
import re
import sys


# ──────────────────────────────────────────────
# DENY — Block outright. Require manual execution.
# ──────────────────────────────────────────────
DENY_PATTERNS = [
    # SQL destruction
    (r"\bDROP\s+(DATABASE|TABLE|SCHEMA|INDEX)\b", "DROP DATABASE/TABLE/SCHEMA/INDEX"),
    (r"\bTRUNCATE\s+TABLE\b", "TRUNCATE TABLE"),
    (r"\bDELETE\s+FROM\b.{0,60}\bWHERE\s+1\s*=\s*1\b", "DELETE WHERE 1=1 (full table)"),
    # Filesystem destruction
    (r"\bFORMAT\s+[A-Z]:\b", "FORMAT drive"),
    (r"\brm\s+(-rf|-fr|-r\s+-f|-f\s+-r)\s+/", "rm -rf /path"),
    (r"\brmdir\s+/s\s+/q\s+[A-Z]:\\?\s*$", "rmdir /s /q drive root"),
    (r"\bdel\s+/[sS]\s+.*\*\.\*", "del /s *.* (mass delete)"),
    (r"Remove-Item\s+.*-Recurse.*-Force.*[A-Z]:\\?\s*$", "Remove-Item -Recurse -Force drive root"),
    (r"\bshred\b", "shred"),
    (r"> /dev/sd[a-z]\b", "write to raw disk device"),
    (r"\bdd\s+if=.*of=/dev/sd", "dd to block device"),
    # Git destruction
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    (r"\bgit\s+clean\s+-[a-z]*f[a-z]*\b", "git clean -f"),
    (r"\bgit\s+push\s+.*--force\b", "git push --force"),
    (r"\bgit\s+push\s+-f\b", "git push -f"),
    # Infrastructure destruction
    (r"\bterraform\s+destroy\b", "terraform destroy"),
    (r"\bkubectl\s+delete\b", "kubectl delete"),
    (r"\bdocker\s+system\s+prune\b", "docker system prune"),
    # Alembic downgrade
    (r"\balembic\s+downgrade\s+(base|zero|-[0-9]+)\b", "alembic downgrade to base/zero"),
    # Credential changes
    (r"\bpasswd\b", "passwd (credential change)"),
    (r"\bchpasswd\b", "chpasswd (credential change)"),
]

# ──────────────────────────────────────────────
# ASK — Require explicit human approval via Antigravity review.
# ──────────────────────────────────────────────
ASK_PATTERNS = [
    (r"\bgit\s+push\b", "git push"),
    (r"\bgit\s+reset\b", "git reset"),
    (r"\bgit\s+clean\b", "git clean"),
    (r"\bgit\s+rebase\b", "git rebase"),
    (r"\bdocker\s+(rm|rmi|stop|kill|restart)\b", "docker container/image operation"),
    (r"\bdrop\b", "drop (possible DB operation)"),
    (r"\btruncate\b", "truncate"),
    (r"\bpurge\b", "purge"),
    (r"\balembic\s+downgrade\b", "alembic downgrade"),
    (r"\balembic\s+upgrade\b", "alembic upgrade (schema migration)"),
    (r"(?i)(production|prod)\b", "production environment reference"),
    (r"(?i)\b(secret|credential|password|token|api.?key)\b", "credential-related command"),
    (r"(?i)\bcurl\s+.*-X\s+(DELETE|PUT|POST)\b", "curl mutation request"),
    (r"(?i)\bwget\s+.*(\.sh|\.bat|\.ps1|\.exe)\b", "downloading executable"),
    (r"(?i)\biwr\b.*\.sh\b", "Invoke-WebRequest for script"),
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Cannot parse — allow rather than block legitimate work unexpectedly
        sys.stdout.write(json.dumps({"decision": "allow"}))
        return

    args = data.get("toolCall", {}).get("args", {}) or data.get("args", {}) or data
    cmd = args.get("CommandLine", "") or args.get("command", "") or data.get("command", "") or ""

    if not cmd or not isinstance(cmd, str):
        sys.stdout.write(json.dumps({"decision": "allow"}))
        return

    # Check DENY list first
    for pattern, label in DENY_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            sys.stdout.write(json.dumps({
                "decision": "deny",
                "reason": (
                    f"BLOCKED — Dangerous operation detected: [{label}] in command: "
                    f"'{cmd[:120]}'. "
                    "This command requires explicit human review and manual execution. "
                    "If intentional, run the command manually in a terminal after careful review."
                )
            }))
            return

    # Check ASK list
    for pattern, label in ASK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            sys.stdout.write(json.dumps({
                "decision": "ask",
                "reason": (
                    f"Sensitive operation requires approval: [{label}] "
                    f"in command: '{cmd[:120]}'"
                )
            }))
            return

    # Default: allow
    sys.stdout.write(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
