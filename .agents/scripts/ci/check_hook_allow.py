#!/usr/bin/env python
"""CI: Verify check_dangerous_cmd allows safe commands."""
import json
import subprocess
import sys

safe_cmd = json.dumps({"CommandLine": "git status"})
result = subprocess.run(
    [sys.executable, ".agents/scripts/check_dangerous_cmd.py"],
    input=safe_cmd,
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)
if data.get("decision") != "allow":
    print("FAIL - expected allow, got:", data)
    sys.exit(1)
print("OK - dangerous_cmd hook: allow for safe command")
