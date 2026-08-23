#!/usr/bin/env python
"""CI: Run Bandit SAST scan on src/ and fail on any medium/high issues."""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "bandit", "-r", "src/", "--ini", ".bandit", "-q"],
    capture_output=True,
    text=True,
)

print(result.stdout)
if result.returncode != 0:
    print("FAIL - Bandit found security issues:")
    print(result.stderr)
    sys.exit(1)

print("OK - Bandit: no medium/high severity issues")
