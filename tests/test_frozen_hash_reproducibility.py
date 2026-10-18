"""Frozen artifact hashes must reproduce on every platform's checkout.

The recorded values below come from the frozen manifests and protocols named
next to each entry; they are compared against the working-tree bytes.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

FROZEN = [
    # PHASE15_DATASET_FREEZE.json, FREE_REPLICATION_V1_MANIFEST.json, phase15_runner.FROZEN_DATASET_HASH
    ("experiments/phase15/phase15_cases.jsonl", "af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48"),
    # reports/audit/VALIDATION_PACKAGE_2026-10-13.md
    ("experiments/architecture_baseline/FREE_REPLICATION_V1_MANIFEST.json", "5a91939f75ce1773991748595030f3c372e04c04acc8b5e5fb6cd6836c0ade9e"),
    # ANNOTATION_COMPLETION_PROTOCOL.md, frozen retrieval artifacts (Rule 15)
    ("experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced/runner_real_hardened.py", "774c9d65cae1b6e83a945d5c773d8fc07ff0043c806975428d8b4e5ddc13f9a5"),
    ("experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced/f0_results.jsonl", "15b19e54b03ddbd2bc513cac3800a73303dac11408db8d6484b62829b4c0846a"),
    ("experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced/f3_results.jsonl", "45e54b6143531747f6fde9778bc0391f26cc90d09ac041708005ef6dd6819f36"),
    ("experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced/debug_records.jsonl", "6cbd595a4afb1f153cdc5fff8d2edcf03241e4ad1319018afdc73ddf2366d362"),
    ("experiments/evidence_snapshots/retrieval-v3-real/documents.json", "e4346ad15ec1f74af9ecc010ef822503eb44638f1020e7f0fcb51ad5c58f42f7"),
    # TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json
    ("track_a_annotation/decision_batches/TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt", "374351cf42f177484b26962f92ffdca3ed1d6862a73211d714816b958610cab4"),
    ("track_a_annotation/decision_batches/TRACK_A_LLM_SYSTEM_PROMPT_V2.txt", "f6433f2c57a830088c3cf70340349c271d6b03df17935d862dfb318483604bd3"),
    # V1_2_PROMPT_INSTANTIATION_REMEDIATION.md
    ("experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt", "e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c"),
]


@pytest.mark.parametrize("path,expected", FROZEN, ids=[p for p, _ in FROZEN])
def test_frozen_artifact_hash_reproduces(path, expected):
    assert hashlib.sha256((REPO / path).read_bytes()).hexdigest() == expected


def test_every_crlf_hashed_file_is_pinned():
    result = subprocess.run(
        [sys.executable, "scripts/audit_frozen_hash_line_endings.py", "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]
