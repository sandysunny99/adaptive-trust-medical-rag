import json
import subprocess
from pathlib import Path

SCANNER_PATH = Path(__file__).parents[1] / ".agents" / "scripts" / "pre_commit_secret_scan.py"


def _run_scanner(code: str) -> dict:
    payload = json.dumps({"toolCall": {"args": {"CodeContent": code}}})
    proc = subprocess.run(
        ["python", str(SCANNER_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"Scanner failed: {proc.stderr}")
    return json.loads(proc.stdout)


def test_hardcoded_gemini_api_key_is_denied():
    result = _run_scanner('GEMINI_API_KEY = "s3cr3tV4lu3_1234567890"')
    assert result["decision"] == "deny", f"Got: {result}"
    assert "Hardcoded API key" in result["reason"], f"Got: {result}"


def test_envvar_reference_is_allowed():
    result = _run_scanner('api_key = os.getenv("GEMINI_API_KEY")')
    assert result["decision"] == "allow", f"Got: {result}"
