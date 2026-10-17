"""Frozen Track A prompt hashes are SHA-256 of the raw prompt bytes.

The hashes in TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json were recorded by
track_a_annotation/decision_batches/gen_final_v14.py, which reads each prompt with "rb", on a
Windows checkout: the adjudication prompt's recorded hash is of its CRLF bytes. The engine used
to hash the text it read in text mode (CRLF turned into LF), so it rejected the true frozen file.
It now hashes the raw bytes; an LF copy of a CRLF-frozen prompt is a different file and is
rejected. The folder .gitattributes pins the prompt to CRLF so every checkout reproduces it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.annotation.engine import AIAnnotationEngine, PromptHashMismatchError
from adaptive_trust_medical_rag.annotation.schemas import AnnotationSessionConfig

ROOT = Path(__file__).resolve().parents[1]
BATCHES = Path("track_a_annotation") / "decision_batches"
ADJ = "TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt"
FROZEN = "TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json"
SCHEMA = {"type": "object", "properties": {"verdict": {"type": "string"}}}
PROMPT_LINES = ["You adjudicate synthetic evidence.", "Query: {query}", "Evidence:", "{evidence}", ""]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def workspace(tmp_path: Path, adjudication: bytes, frozen_adjudication: bytes) -> Path:
    """A synthetic workspace whose frozen manifest records the hash of ``frozen_adjudication``."""
    d = tmp_path / BATCHES
    d.mkdir(parents=True)
    system, challenge = b"System prompt without line breaks.", b"Challenge prompt without line breaks."
    (d / "TRACK_A_LLM_SYSTEM_PROMPT_V2.txt").write_bytes(system)
    (d / "TRACK_A_LLM_CHALLENGE_PROMPT_V2.txt").write_bytes(challenge)
    (d / ADJ).write_bytes(adjudication)
    (d / "TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
    (d / FROZEN).write_text(json.dumps({
        "system_prompt_sha256": sha(system),
        "challenge_prompt_sha256": sha(challenge),
        "adjudication_prompt_sha256": sha(frozen_adjudication),
        "track_a_adjudication_schema_sha256": sha(json.dumps(SCHEMA, sort_keys=True, separators=(",", ":")).encode()),
    }), encoding="utf-8")
    return tmp_path


def engine(ws: Path) -> AIAnnotationEngine:
    return AIAnnotationEngine(AnnotationSessionConfig(provider="mock"), workspace_dir=ws)


CRLF = "\r\n".join(PROMPT_LINES).encode("utf-8")
LF = "\n".join(PROMPT_LINES).encode("utf-8")


def test_a_crlf_prompt_frozen_as_crlf_bytes_verifies(tmp_path):
    e = engine(workspace(tmp_path, CRLF, CRLF))
    assert e.prompt_hashes["adjudication_prompt_sha256"] == sha(CRLF)


def test_an_lf_prompt_frozen_as_lf_bytes_verifies(tmp_path):
    e = engine(workspace(tmp_path, LF, LF))
    assert e.prompt_hashes["adjudication_prompt_sha256"] == sha(LF)


def test_an_lf_copy_of_a_crlf_frozen_prompt_fails_closed(tmp_path):
    with pytest.raises(PromptHashMismatchError, match="adjudication_prompt_sha256.*modified from frozen baseline"):
        engine(workspace(tmp_path, LF, CRLF))


def test_a_crlf_copy_of_an_lf_frozen_prompt_fails_closed(tmp_path):
    with pytest.raises(PromptHashMismatchError, match="adjudication_prompt_sha256"):
        engine(workspace(tmp_path, CRLF, LF))


def test_the_prompt_text_is_still_read_as_text(tmp_path):
    e = engine(workspace(tmp_path, CRLF, CRLF))
    assert "\r" not in e.adjudication_prompt_template
    assert e.format_prompt("q", "ev").endswith("Evidence:\nev\n")


def test_the_repository_prompts_verify_against_the_recorded_hashes():
    e = engine(ROOT)
    frozen = json.loads((ROOT / BATCHES / FROZEN).read_text(encoding="utf-8"))
    for key in ("system_prompt_sha256", "adjudication_prompt_sha256", "challenge_prompt_sha256",
                "track_a_adjudication_schema_sha256"):
        assert e.prompt_hashes[key] == frozen[key], key


def test_the_recorded_adjudication_hash_is_of_the_crlf_bytes():
    raw = (ROOT / BATCHES / ADJ).read_bytes()
    frozen = json.loads((ROOT / BATCHES / FROZEN).read_text(encoding="utf-8"))["adjudication_prompt_sha256"]
    assert b"\r\n" in raw and sha(raw) == frozen
    assert sha(raw.replace(b"\r\n", b"\n")) != frozen


def test_the_adjudication_prompt_is_pinned_to_crlf_for_every_checkout():
    out = subprocess.run(["git", "check-attr", "text", "eol", "--", str(BATCHES / ADJ)],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert "text: set" in out and "eol: crlf" in out
