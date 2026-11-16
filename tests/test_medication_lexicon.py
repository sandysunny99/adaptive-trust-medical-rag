"""The pinned RxNorm medication lexicon: provenance, integrity and fail-closed loading (round 6)."""

import hashlib
import json
import shutil

import pytest

from adaptive_trust_medical_rag.normalization.medication_lexicon import (
    LEXICON_DIR,
    LexiconUnavailable,
    load_lexicon,
)

MANIFEST = json.loads((LEXICON_DIR / "MANIFEST.json").read_text(encoding="utf-8"))


def test_every_recorded_hash_matches_its_file():
    assert hashlib.sha256((LEXICON_DIR / MANIFEST["lexicon"]).read_bytes()).hexdigest() == MANIFEST["lexicon_sha256"]
    for path, digest in MANIFEST["source_files_sha256"].items():
        assert hashlib.sha256((LEXICON_DIR / path).read_bytes()).hexdigest() == digest, path


def test_the_lexicon_is_exactly_the_api_responses_it_was_built_from():
    entries = sorted(({"rxcui": c["rxcui"], "name": c["name"], "tty": tty}
                      for tty in ("IN", "PIN", "MIN", "BN")
                      for c in json.loads((LEXICON_DIR / "source" / f"allconcepts_{tty}.json").read_bytes())
                      ["minConceptGroup"]["minConcept"]), key=lambda e: (e["tty"], e["name"], e["rxcui"]))
    release = json.loads((LEXICON_DIR / "source" / "version.json").read_bytes())["version"]
    rebuilt = json.dumps({"format": "rxnorm-prescribable-lexicon/1", "release": release, "entries": entries},
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(rebuilt).hexdigest() == MANIFEST["lexicon_sha256"]
    assert MANIFEST["release"] == release == "05-Oct-2026"


def test_the_pinned_lexicon_loads_with_its_counts():
    lex = load_lexicon()
    assert (lex.release, lex.size) == ("05-Oct-2026", 12929) == (MANIFEST["release"], MANIFEST["counts"]["entries"])


@pytest.fixture
def copy(tmp_path):
    shutil.copytree(LEXICON_DIR, tmp_path / "lex")
    return tmp_path / "lex"


def test_a_missing_lexicon_is_unavailable(copy):
    (copy / MANIFEST["lexicon"]).unlink()
    with pytest.raises(LexiconUnavailable, match="cannot read"):
        load_lexicon(copy)


def test_an_altered_lexicon_is_unavailable(copy):
    path = copy / MANIFEST["lexicon"]
    path.write_bytes(path.read_bytes().replace(b'"name":"furosemide"', b'"name":"furosemidX"'))
    with pytest.raises(LexiconUnavailable, match="does not match its recorded SHA-256"):
        load_lexicon(copy)


def _rehash(copy, body: bytes):
    (copy / MANIFEST["lexicon"]).write_bytes(body)
    manifest = dict(MANIFEST, lexicon_sha256=hashlib.sha256(body).hexdigest())
    (copy / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize("body", [
    b"not json",
    b'{"format":"rxnorm-prescribable-lexicon/2","release":"05-Oct-2026","entries":[]}',
    b'{"format":"rxnorm-prescribable-lexicon/1","release":"01-Jan-2020","entries":[]}',
    b'{"format":"rxnorm-prescribable-lexicon/1","release":"05-Oct-2026","entries":[{"rxcui":"1","name":"x","tty":"SCD"}]}',
    b'{"format":"rxnorm-prescribable-lexicon/1","release":"05-Oct-2026"}',
], ids=["corrupt", "unsupported format", "release mismatch", "unsupported term type", "no entries"])
def test_a_malformed_lexicon_with_a_matching_hash_is_still_unavailable(copy, body):
    _rehash(copy, body)
    with pytest.raises(LexiconUnavailable):
        load_lexicon(copy)


def test_a_missing_manifest_is_unavailable(copy):
    (copy / "MANIFEST.json").unlink()
    with pytest.raises(LexiconUnavailable, match="cannot read"):
        load_lexicon(copy)
