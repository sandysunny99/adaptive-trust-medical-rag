#!/usr/bin/env python
"""CI: Verify inject_medical_context hook returns injectSteps."""

import json
import subprocess
import sys

sys.path.insert(0, "src")

result = subprocess.run(
    [sys.executable, ".agents/scripts/inject_medical_context.py"],
    input="{}",
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print("FAIL - hook returned non-zero:", result.returncode)
    sys.exit(1)
data = json.loads(result.stdout)
if "injectSteps" not in data:
    print("FAIL - injectSteps missing from hook output:", data)
    sys.exit(1)
print("OK - inject_medical_context hook: injectSteps present")
