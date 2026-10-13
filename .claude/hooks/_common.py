"""Shared helpers for the Claude Code hook adapters.

The detection logic lives in `.agents/scripts/` (also exercised by CI). These
adapters only translate Claude Code's PreToolUse payload into calls on that
logic and translate the result back into Claude Code's decision format.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_SCRIPTS = PROJECT_ROOT / ".agents" / "scripts"


def load_agent_script(name: str) -> ModuleType:
    path = AGENT_SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"agents_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_payload() -> dict:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def emit(decision: str, reason: str) -> None:
    """Write a PreToolUse decision ("deny" or "ask"). Allow = write nothing."""
    sys.stdout.write(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
