#!/usr/bin/env python3
"""
Security Audit Orchestrator — Antigravity Medical RAG
Runs local security validations:
1. Gitleaks (Secrets Detection)
2. Ruff (Linting & Code Quality)
3. Bandit (Python SAST)
4. Semgrep (Semantic Code Analysis)
5. Trivy (Supply Chain & Dependency Audit)
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output even on legacy Windows console charmaps
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def safe_print(text: str, is_error: bool = False) -> None:
    target = sys.stderr if is_error else sys.stdout
    try:
        print(text, file=target)
    except UnicodeEncodeError:
        safe_text = text.encode("ascii", "backslashreplace").decode("ascii")
        print(safe_text, file=target)


def run_check(name: str, cmd: list[str], allow_warnings: bool = False) -> bool:
    safe_print(f"\n{'=' * 60}\n[RUNNING] {name}\n{'=' * 60}")
    safe_print(f"Command: {' '.join(cmd)}")
    try:
        res = subprocess.run(  # nosec B603
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if res.stdout:
            safe_print(res.stdout)
        if res.stderr:
            safe_print(res.stderr, is_error=True)
        if res.returncode == 0:
            safe_print(f"[PASS] {name} passed successfully.")
            return True
        else:
            if allow_warnings:
                safe_print(f"[WARN] {name} exited with code {res.returncode} (non-fatal).")
                return True
            safe_print(f"[FAIL] {name} failed with exit code {res.returncode}.")
            return False
    except Exception as e:
        safe_print(f"[ERROR] Could not execute {name}: {e}")
        return False


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    safe_print(f"Starting Security Audit for Medical RAG Platform at: {workspace}")

    results = {}

    # 1. Gitleaks
    gitleaks_bin = shutil.which("gitleaks")
    if gitleaks_bin:
        results["Gitleaks"] = run_check(
            "Gitleaks Secret Scan",
            [gitleaks_bin, "detect", "--source", str(workspace), "--verbose"],
        )
    else:
        safe_print("\n[SKIP] Gitleaks not found in PATH.")

    # 2. Ruff
    results["Ruff"] = run_check(
        "Ruff Code Quality & Lint",
        ["uv", "run", "ruff", "check", "."],
    )

    # 3. Bandit
    results["Bandit"] = run_check(
        "Bandit Python SAST",
        ["uv", "run", "bandit", "-r", ".", "-c", "pyproject.toml"],
    )

    # 4. Semgrep
    results["Semgrep"] = run_check(
        "Semgrep Security Analysis",
        ["uv", "run", "semgrep", "--config", "auto", "--quiet", "."],
        allow_warnings=True,
    )

    # 5. Trivy
    trivy_bin = shutil.which("trivy")
    if trivy_bin:
        results["Trivy"] = run_check(
            "Trivy Filesystem Vulnerability Scan",
            [trivy_bin, "fs", "--severity", "CRITICAL,HIGH", "."],
            allow_warnings=True,
        )
    else:
        safe_print("\n[SKIP] Trivy not found in PATH.")

    safe_print(f"\n{'=' * 60}\nSECURITY AUDIT SUMMARY\n{'=' * 60}")
    all_passed = True
    for tool, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        safe_print(f" - {tool:15}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        safe_print("\nALL SECURITY CHECKS PASSED. Ready for commit / PR.")
        return 0
    else:
        safe_print("\nONE OR MORE CRITICAL SECURITY CHECKS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
