#!/usr/bin/env python
"""CI: Verify pre_commit_secret_scan allows clean code."""
import json
import subprocess
import sys

clean_code = json.dumps({"CodeContent": "x = 1 + 2"})
result = subprocess.run(
    [sys.executable, ".agents/scripts/pre_commit_secret_scan.py"],
    input=clean_code,
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)
if data.get("decision") != "allow":
    print("FAIL - expected allow, got:", data)
    sys.exit(1)
print("OK - secret_scan hook: allow for clean code")
