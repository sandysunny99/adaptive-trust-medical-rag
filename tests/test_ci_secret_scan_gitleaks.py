"""The CI secret-scan hook's gitleaks layer (.agents/scripts/ci/pre_commit_secret_scan.py).

gitleaks 8.30 rejects ``--quiet``, and the hook used to read that failure as a found secret,
so it denied every file. The hook now passes only flags gitleaks accepts, treats exit 1 as a
found secret and any other non-zero exit as a scan that could not run; both still block.
gitleaks itself is replaced here, so these tests run without the binary.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).parents[1] / ".agents" / "scripts" / "ci" / "pre_commit_secret_scan.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("ci_secret_scan_hook", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hook(monkeypatch):
    module = load_hook()
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(module.shutil, "which", lambda name: "gitleaks")
    return module


def fake_gitleaks(monkeypatch, module, returncode: int) -> list[list[str]]:
    calls: list[list[str]] = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", run)
    return calls


def test_the_hook_passes_only_flags_gitleaks_8_30_accepts(hook, monkeypatch):
    calls = fake_gitleaks(monkeypatch, hook, 0)
    assert hook.scan_with_gitleaks("x = 1\n") == []
    (cmd,) = calls
    assert cmd[1:2] == ["detect"] and "--no-git" in cmd
    assert "--quiet" not in cmd
    assert cmd[cmd.index("--exit-code") + 1] == "1"
    assert "--redact" in cmd and "--no-banner" in cmd


def test_a_found_secret_blocks(hook, monkeypatch):
    fake_gitleaks(monkeypatch, hook, 1)
    assert hook.scan_with_gitleaks("x = 1\n") == ["GITLEAKS DETECTED SECRETS — run `gitleaks detect` for details"]


@pytest.mark.parametrize("returncode", [2, 126, -1])
def test_a_scan_that_could_not_run_still_blocks_but_says_so(hook, monkeypatch, returncode):
    fake_gitleaks(monkeypatch, hook, returncode)
    (finding,) = hook.scan_with_gitleaks("x = 1\n")
    assert finding.startswith(f"GITLEAKS COULD NOT RUN (exit {returncode})")
    assert "DETECTED SECRETS" not in finding


def decision(hook, monkeypatch, capsys, content: str) -> dict:
    import io
    import json

    payload = json.dumps({"args": {"TargetFile": "src/example.py", "CodeContent": content}})
    monkeypatch.setattr(hook.sys, "stdin", io.StringIO(payload))
    hook.main()
    return json.loads(capsys.readouterr().out)


def test_a_failed_scan_is_not_reported_as_a_found_secret(hook, monkeypatch, capsys):
    fake_gitleaks(monkeypatch, hook, 126)
    result = decision(hook, monkeypatch, capsys, "def add(a, b):\n    return a + b\n")
    assert result["decision"] == "deny"
    assert result["reason"].startswith("SECRET SCAN COULD NOT RUN")
    assert "SECRET DETECTED" not in result["reason"]


def test_a_found_secret_is_reported_as_one(hook, monkeypatch, capsys):
    fake_gitleaks(monkeypatch, hook, 1)
    result = decision(hook, monkeypatch, capsys, "def add(a, b):\n    return a + b\n")
    assert result["decision"] == "deny" and result["reason"].startswith("SECRET DETECTED")


def test_clean_content_with_a_clean_scan_is_allowed(hook, monkeypatch, capsys):
    fake_gitleaks(monkeypatch, hook, 0)
    assert decision(hook, monkeypatch, capsys, "def add(a, b):\n    return a + b\n") == {"decision": "allow"}
