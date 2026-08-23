"""
Migration utilities for Adaptive Trust Medical RAG.

Provides offline SQL generation (for review/deployment without a live DB)
and migration version introspection used in tests and CI.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ALEMBIC_VERSIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "alembic" / "versions"


def list_migration_versions() -> list[dict[str, Any]]:
    """
    Enumerate all migration version files and return their metadata.

    Returns a list of dicts: {revision, down_revision, path, tables_created}
    sorted by revision ID.
    """
    versions = []
    for py_file in sorted(ALEMBIC_VERSIONS_DIR.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        text = py_file.read_text(encoding="utf-8")

        # Handle both  revision = "x"  and  revision: str = "x"
        rev_match = re.search(
            r'^revision(?:\s*:\s*\S+)?\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE
        )
        down_match = re.search(
            r"^down_revision(?:\s*:\s*\S+(?:\[.*?\])?)?\s*=\s*(.+)$", text, re.MULTILINE
        )

        revision = rev_match.group(1) if rev_match else "unknown"
        down_raw = down_match.group(1).strip() if down_match else "None"
        # Strip type hints from down_revision value  e.g.  None  or  "abc123"
        down_raw_clean = re.sub(r"#.*$", "", down_raw).strip()
        down_revision = None if down_raw_clean in ("None", "null") else down_raw_clean.strip("\"'")

        # Extract tables created by op.create_table calls
        tables = re.findall(r'op\.create_table\(\s*["\']([^"\']+)["\']', text)

        versions.append(
            {
                "revision": revision,
                "down_revision": down_revision,
                "path": str(py_file),
                "tables_created": tables,
                "filename": py_file.name,
            }
        )

    return sorted(versions, key=lambda v: v["revision"])


def get_migration_chain() -> list[str]:
    """
    Return the ordered migration chain from root to latest.

    Returns revision IDs in upgrade order: [first, ..., latest].
    """
    versions = list_migration_versions()
    if not versions:
        return []

    # Build graph: down_revision -> revision
    by_down: dict[Any, dict[str, Any]] = {v["down_revision"]: v for v in versions}

    chain = []
    current = by_down.get(None)
    while current is not None:
        chain.append(current["revision"])
        current = by_down.get(current["revision"])
    return chain


def verify_migration_chain() -> list[str]:
    """
    Verify the migration chain has no gaps or cycles.

    Returns list of error strings (empty = valid).
    """
    versions = list_migration_versions()
    errors = []

    revisions = {v["revision"] for v in versions}
    for v in versions:
        dr = v["down_revision"]
        if dr is not None and dr not in revisions:
            errors.append(f"Migration {v['revision']} references missing down_revision: {dr}")

    # Detect cycles
    chain = get_migration_chain()
    if len(chain) != len(versions):
        errors.append(
            f"Migration chain length {len(chain)} != "
            f"total versions {len(versions)}. Possible cycle or branch."
        )
    return errors


def generate_offline_sql(revision: str = "head") -> str:
    """
    Generate SQL for offline review without a live database.

    This uses Alembic's offline mode which writes SQL to stdout/string.
    Returns the generated DDL as a string, or an info message if unavailable.

    Args:
        revision: Target revision ("head" = latest, or specific revision ID).
    """
    try:
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "upgrade",
                revision,
                "--sql",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        return f"-- alembic offline SQL generation failed:\n-- {result.stderr}"
    except Exception as exc:
        return f"-- Error generating offline SQL: {exc}"
