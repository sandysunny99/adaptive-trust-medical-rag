#!/usr/bin/env python3
"""Find tracked files whose recorded SHA-256 only matches their CRLF form.

Many frozen hashes in this repository were computed on a Windows checkout,
where git converts LF to CRLF. On an LF checkout (Linux CI, cloud runners)
those files hash differently and every preflight comparing against the frozen
value fails. This script lists such files so .gitattributes can pin them to
eol=crlf; it never edits a frozen artifact or a recorded hash.

Usage:
    python scripts/audit_frozen_hash_line_endings.py            # report
    python scripts/audit_frozen_hash_line_endings.py --check    # exit 1 if any file is unpinned
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HEX64 = re.compile(rb"\b[0-9a-fA-F]{64}\b")
RECORD_SUFFIXES = (".json", ".jsonl", ".md", ".txt", ".py", ".csv")
MAX_BYTES = 30_000_000


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout
    return [p.decode() for p in out.split(b"\0") if p]


def read(path: str) -> bytes | None:
    p = REPO_ROOT / path
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        return p.read_bytes()
    except OSError:
        return None


def recorded_hashes(files: list[str]) -> set[str]:
    hashes: set[str] = set()
    for f in files:
        if f.endswith(RECORD_SUFFIXES):
            data = read(f)
            if data:
                hashes.update(h.decode().lower() for h in HEX64.findall(data))
    return hashes


def crlf_only_files(files: list[str], recorded: set[str]) -> list[str]:
    result = []
    for f in files:
        data = read(f)
        if data is None or b"\0" in data[:8000]:
            continue
        lf = data.replace(b"\r\n", b"\n")
        lf_hash = hashlib.sha256(lf).hexdigest()
        crlf_hash = hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest()
        if crlf_hash != lf_hash and crlf_hash in recorded and lf_hash not in recorded:
            result.append(f)
    return result


def pinned_crlf(files: list[str]) -> set[str]:
    out = subprocess.run(
        ["git", "check-attr", "eol", "--stdin", "-z"],
        cwd=REPO_ROOT,
        input=b"\0".join(f.encode() for f in files),
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    # Output is triples: path, attribute, value.
    return {out[i].decode() for i in range(0, len(out) - 2, 3) if out[i + 2] == b"crlf"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if any CRLF-hashed file is not pinned")
    args = parser.parse_args()

    files = tracked_files()
    crlf = crlf_only_files(files, recorded_hashes(files))
    unpinned = sorted(set(crlf) - pinned_crlf(crlf)) if crlf else []
    for f in crlf:
        print(f"{'UNPINNED' if f in unpinned else 'pinned  '} {f}")
    print(f"{len(crlf)} file(s) recorded in CRLF form, {len(unpinned)} not pinned to eol=crlf")
    return 1 if (args.check and unpinned) else 0


if __name__ == "__main__":
    sys.exit(main())
