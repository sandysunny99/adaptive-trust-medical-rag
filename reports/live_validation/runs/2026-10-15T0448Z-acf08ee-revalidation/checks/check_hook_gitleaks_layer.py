"""Exercise the CI secret-scan hook's gitleaks layer and its regex layer directly.

The fake credential is random and generated in memory (never written to the repository); it only
has the shape of a GitHub token so the rules fire. Usage: python check_hook_gitleaks_layer.py <hook.py>
"""
import importlib.util
import secrets
import string
import sys

spec = importlib.util.spec_from_file_location("hook", sys.argv[1])
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

fake = "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
cases = {
    "fake GitHub-token-shaped string": f'GH = "{fake}"\n',
    "clean code": "def add(a, b):\n    return a + b\n",
    "env-var reference": 'import os\nTOKEN = os.environ["GITHUB_TOKEN"]\n',
}
ok = True
for name, content in cases.items():
    g, r = hook.scan_with_gitleaks(content), hook.scan_with_regex(content)
    expect = name.startswith("fake")
    passed = bool(g) == expect and bool(r) == expect
    ok &= passed
    print(f"{'PASS' if passed else 'FAIL'}  {name}: gitleaks={g or 'clean'}  regex={r or 'clean'}")
sys.exit(0 if ok else 1)
