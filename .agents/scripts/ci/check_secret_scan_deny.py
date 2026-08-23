#!/usr/bin/env python
"""CI: Verify pre_commit_secret_scan denies code with secrets."""

import json
import subprocess
import sys

# Build token from parts to avoid triggering gitleaks on this file itself
prefix = "g" + "h" + "p" + "_"
fake_token = prefix + "0" * 36
secret_code = json.dumps({"CodeContent": "token = " + fake_token})
result = subprocess.run(
    [sys.executable, ".agents/scripts/pre_commit_secret_scan.py"],
    input=secret_code,
    capture_output=True,
    text=True,
)
data = json.loads(result.stdout)
if data.get("decision") != "deny":
    print("FAIL - expected deny, got:", data)
    sys.exit(1)
print("OK - secret_scan hook: deny for code with fake token")
