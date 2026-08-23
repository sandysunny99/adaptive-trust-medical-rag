#!/usr/bin/env python
"""CI: Verify check_dangerous_cmd denies destructive commands."""
import json
import subprocess
import sys

# Construct from parts so no literal dangerous string appears in CI logs
parts = ["r" + "m", "-" + "r" + "f", "/"]
dangerous_cmd = json.dumps({"CommandLine": " ".join(parts)})
result = subprocess.run(
    [sys.executable, ".agents/scripts/check_dangerous_cmd.py"],
    input=dangerous_cmd,
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)
if data.get("decision") != "deny":
    print("FAIL - expected deny, got:", data)
    sys.exit(1)
print("OK - dangerous_cmd hook: deny for destructive command")
