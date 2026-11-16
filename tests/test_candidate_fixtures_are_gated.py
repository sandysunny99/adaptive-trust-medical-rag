"""The relationship candidates shipped as test fixtures stay pending and are never loaded.

tests/fixtures/{rel_live_0003,rel_live_0004,food_0001}_candidate hold real DailyMed label text
for candidate datasets that no authorized reviewer has graded or approved. They exist so the
loader and verification tests run in a fresh checkout. Tests may copy one into tmp_path and
approve the copy; the shipped files must stay unapproved, ungraded and outside the live data.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.services.live_relationships import load_relationship_store

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
LIVE_DATA = ROOT / "data" / "live_medical"
CANDIDATES = ["rel_live_0003_candidate", "rel_live_0004_candidate", "food_0001_candidate"]
FILES = (
    "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
    "LIVE_RELATIONSHIP_RECORDS_V2.json",
    "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json",
)


def read(name: str, file: str):
    return json.loads((FIXTURES / name / file).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", CANDIDATES)
def test_the_shipped_candidate_is_pending_with_no_approver(name):
    manifest = read(name, "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json")
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL"
    assert not (manifest.get("approval") or {}).get("approved_by")
    assert not (manifest.get("approval") or {}).get("approved_at")


@pytest.mark.parametrize("name", CANDIDATES)
def test_no_shipped_record_carries_a_severity_grade(name):
    for record in read(name, "LIVE_RELATIONSHIP_RECORDS_V2.json")["records"]:
        assert record["severity"] == "UNGRADED"


@pytest.mark.parametrize("name", CANDIDATES)
def test_the_loader_loads_nothing_from_the_shipped_candidate(name, tmp_path):
    for file in FILES:
        shutil.copyfile(FIXTURES / name / file, tmp_path / file)
    store = load_relationship_store([], str(tmp_path))
    assert store.status != "APPROVED"
    assert store.records == () and store.evidence == ()


# Candidates the researcher has approved into the live data, each in its own v2/<folder>
# (FOOD-0001 approved 2026-11-14). Every other candidate must stay out of the live data.
APPROVED_IN_LIVE = {"food_0001_candidate": "food_0001"}


def candidate_ids(name: str) -> list[str]:
    ids = [r["record_id"] for r in read(name, "LIVE_RELATIONSHIP_RECORDS_V2.json")["records"]]
    evidence = read(name, "LIVE_RELATIONSHIP_EVIDENCE_V2.json")
    chunks = evidence if isinstance(evidence, list) else evidence.get("evidence", [])
    return ids + [c["chunk_id"] for c in chunks]


@pytest.mark.parametrize("name", [c for c in CANDIDATES if c not in APPROVED_IN_LIVE])
def test_no_pending_candidate_record_or_chunk_is_in_the_live_data(name):
    ids = candidate_ids(name)
    live_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in LIVE_DATA.rglob("*.json")
        if "source_capture" not in p.parts
    )
    assert ids and not [i for i in ids if i in live_text]


@pytest.mark.parametrize("name", sorted(APPROVED_IN_LIVE))
def test_an_approved_candidate_is_live_only_in_its_own_folder_unchanged(name):
    folder = LIVE_DATA / "relationships" / "v2" / APPROVED_IN_LIVE[name]
    ids = candidate_ids(name)
    outside = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in LIVE_DATA.rglob("*.json")
        if "source_capture" not in p.parts and folder not in p.parents
    )
    assert ids and not [i for i in ids if i in outside]
    # The records and evidence are the reviewed files, byte for byte; only the manifest changes.
    for file in ("LIVE_RELATIONSHIP_EVIDENCE_V2.json", "LIVE_RELATIONSHIP_RECORDS_V2.json"):
        assert (folder / file).read_bytes() == (FIXTURES / name / file).read_bytes()
    manifest = json.loads((folder / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "APPROVED"
    assert manifest["approval"]["approved_by"] and manifest["approval"]["approved_at"]
