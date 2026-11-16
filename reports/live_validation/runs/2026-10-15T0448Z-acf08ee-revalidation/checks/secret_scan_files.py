"""Feed each listed file to the repo's CI secret-scan hook (regex + gitleaks) and print the decision."""
import json
import subprocess
import sys
from pathlib import Path

hook = sys.argv[1]
failed = 0
for path in sys.argv[2:]:
    content = Path(path).read_text(encoding="utf-8")
    payload = json.dumps({"args": {"TargetFile": path, "CodeContent": content}})
    out = subprocess.run([sys.executable, hook], input=payload, capture_output=True, text=True).stdout
    decision = json.loads(out or '{"decision": "error"}')
    print(decision.get("decision"), path, decision.get("reason", ""))
    failed += decision.get("decision") != "allow"
print("files", len(sys.argv) - 2, "denied", failed)
sys.exit(1 if failed else 0)
