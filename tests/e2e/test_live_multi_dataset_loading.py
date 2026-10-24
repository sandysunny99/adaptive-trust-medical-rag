"""Several approved V2 datasets, each in its own folder (relationships/v2/<dataset>/).

Uses the three real pending candidates (REL-LIVE-0003, FOOD-0001, REL-LIVE-0004) as fixtures, approved
only inside tmp_path with a test-only severity where a record needs one. The live folder is never touched.
Order: the legacy root dataset ("v2") first, then v2/<folder> in sorted name order.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import _lazy_init_models
from adaptive_trust_medical_rag.services.live_relationships import load_relationship_store

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
LIVE_DIR = ROOT / "data" / "live_medical" / "relationships"
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
NAMES = ("LIVE_RELATIONSHIP_RECORDS_V2.json", "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
         "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json")
FOOD_CHUNK, WARFARIN_CHUNK, SPIRO_CHUNK = (
    "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5", "DAILYMED-884CDBF6-SPL-V8-SEC-7.3", "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1")


def fixture(name: str):
    src = FIX / name
    return [json.loads((src / n).read_text(encoding="utf-8")) for n in NAMES]


def put(root: Path, folder: str | None, name: str, *, approve=True, severity="MODERATE", approval=None, edit=None):
    """Write a fixture as a dataset in root/v2/<folder> (or root itself when folder is None).

    ``edit(records, evidence, manifest)`` changes it before the manifest hashes are computed.
    """
    dest = root if folder is None else root / "v2" / folder
    dest.mkdir(parents=True, exist_ok=True)
    records, evidence, manifest = fixture(name)
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL" and manifest["approval"] is None
    for r in records["records"]:
        assert r["severity"] == "UNGRADED"  # as shipped
        if severity:
            r["severity"] = severity  # test-only grade, not a clinical one
    if edit:
        edit(records, evidence, manifest)
    rec_raw, ev_raw = (json.dumps(records) + "\n").encode(), (json.dumps(evidence) + "\n").encode()
    (dest / NAMES[0]).write_bytes(rec_raw)
    (dest / NAMES[1]).write_bytes(ev_raw)
    manifest.update(records_sha256=hashlib.sha256(rec_raw).hexdigest(), evidence_sha256=hashlib.sha256(ev_raw).hexdigest())
    if approve:
        manifest.update(status="APPROVED", approval=approval or {"approved_by": f"Test {name}", "approved_at": "2026-10-22"})
    (dest / NAMES[2]).write_text(json.dumps(manifest), encoding="utf-8")


def load(root: Path):
    return load_relationship_store(CORPUS, directory=str(root))


def ids(store):
    return sorted(r.record_id for r in store.records), sorted(e["chunk_id"] for e in store.evidence)


def contents(store):
    return store.records, store.evidence


def rejection(store, label):
    return [why for who, why in store.rejected if who == label]


# Test H: nothing, pending, ungraded, incomplete approval.
def test_no_datasets_load_nothing(tmp_path):
    assert ids(load(tmp_path)) == ([], [])


def test_a_pending_dataset_loads_nothing(tmp_path):
    put(tmp_path, "rel_live_0004", "rel_live_0004_candidate", approve=False)
    store = load(tmp_path)
    assert ids(store) == ([], [])
    assert "v2/rel_live_0004: LIVE_RELATIONSHIP_RECORDS_V2 is CANDIDATE_PENDING_RESEARCHER_APPROVAL" in store.reason


def test_an_ungraded_relationship_dataset_is_rejected(tmp_path):
    put(tmp_path, "rel_live_0004", "rel_live_0004_candidate", severity=None)
    store = load(tmp_path)
    assert ids(store) == ([], [])
    assert any(rid == "REL-LIVE-0004" and "UNGRADED" in why for rid, why in store.rejected)


@pytest.mark.parametrize("approval", [{"approved_by": "", "approved_at": "2026-10-22"},
                                      {"approved_by": "Someone", "approved_at": ""}])
def test_incomplete_approval_metadata_is_rejected(tmp_path, approval):
    put(tmp_path, "food_0001", "food_0001_candidate", approval=approval)
    assert ids(load(tmp_path)) == ([], [])


# Test A: the legacy root layout alone.
def test_a_root_level_dataset_alone_loads_as_before(tmp_path):
    put(tmp_path, None, "rel_live_0004_candidate")
    store = load(tmp_path)
    assert ids(store) == (["REL-LIVE-0004"], [WARFARIN_CHUNK])
    assert store.records[0].dataset == store.evidence[0]["dataset"] == "v2"


# Test B: one child dataset.
def test_one_approved_dataset_loads_with_its_provenance(tmp_path):
    put(tmp_path, "food_0001", "food_0001_candidate")
    (chunk,) = load(tmp_path).evidence
    assert chunk["dataset"] == "v2/food_0001"
    assert chunk["dataset_approval"] == {"approved_by": "Test food_0001_candidate", "approved_at": "2026-10-22"}
    # The hashed payload is unchanged: provenance is added beside it, never into the text or its hash.
    (original,) = fixture("food_0001_candidate")[1]
    assert {k: chunk[k] for k in original} == original


# Test C and D: independent datasets together.
def test_food_and_a_relationship_dataset_load_together_with_their_provenance(tmp_path):
    put(tmp_path, "food_0001", "food_0001_candidate")
    put(tmp_path, "rel_live_0004", "rel_live_0004_candidate")
    store = load(tmp_path)
    assert ids(store) == (["REL-LIVE-0004"], [FOOD_CHUNK, WARFARIN_CHUNK])
    assert {e["chunk_id"]: e["dataset"] for e in store.evidence} == {
        FOOD_CHUNK: "v2/food_0001", WARFARIN_CHUNK: "v2/rel_live_0004"}
    assert store.records[0].dataset == "v2/rel_live_0004"


def test_all_three_candidates_coexist_with_their_own_provenance(tmp_path):
    for folder in ("rel_live_0004", "food_0001", "rel_live_0003"):
        put(tmp_path, folder, f"{folder}_candidate")
    store = load(tmp_path)
    assert {r.record_id: (r.dataset, r.source_chunk_id) for r in store.records} == {
        "REL-LIVE-0003": ("v2/rel_live_0003", SPIRO_CHUNK), "REL-LIVE-0004": ("v2/rel_live_0004", WARFARIN_CHUNK)}
    assert {e["chunk_id"]: (e["dataset"], e["dataset_approval"]["approved_by"]) for e in store.evidence} == {
        FOOD_CHUNK: ("v2/food_0001", "Test food_0001_candidate"),
        SPIRO_CHUNK: ("v2/rel_live_0003", "Test rel_live_0003_candidate"),
        WARFARIN_CHUNK: ("v2/rel_live_0004", "Test rel_live_0004_candidate")}
    assert [e["dataset"] for e in store.evidence] == ["v2/food_0001", "v2/rel_live_0003", "v2/rel_live_0004"]


def test_a_root_level_dataset_and_folder_datasets_combine(tmp_path):
    put(tmp_path, None, "food_0001_candidate")
    put(tmp_path, "rel_live_0004", "rel_live_0004_candidate")
    assert {e["dataset"] for e in load(tmp_path).evidence} == {"v2", "v2/rel_live_0004"}


# Test E and I: a later dataset that is mostly new but repeats one chunk ID is rejected whole.
def test_a_later_dataset_repeating_a_chunk_id_is_rejected_whole(tmp_path):
    put(tmp_path, "a_food", "food_0001_candidate")
    before = contents(load(tmp_path))

    def add_the_food_chunk(records, evidence, manifest):  # a new record and chunk, plus one repeated chunk
        evidence.append(fixture("food_0001_candidate")[1][0])
        manifest["standalone_evidence_chunks"] = [FOOD_CHUNK]

    put(tmp_path, "b_warfarin", "rel_live_0004_candidate", edit=add_the_food_chunk)
    alone = load_relationship_store(CORPUS, directory=str(tmp_path / "v2" / "b_warfarin"))
    assert ids(alone) == (["REL-LIVE-0004"], [FOOD_CHUNK, WARFARIN_CHUNK])  # valid on its own
    store = load(tmp_path)
    assert contents(store) == before  # nothing of b_warfarin, a_food unchanged
    assert rejection(store, "v2/b_warfarin") == [
        f"v2/b_warfarin repeats IDs already loaded from another dataset: {FOOD_CHUNK} (in v2/a_food)"]


# Test F: a repeated record ID.
def test_a_later_dataset_repeating_a_record_id_is_rejected_whole(tmp_path):
    put(tmp_path, "a_warfarin", "rel_live_0004_candidate")
    before = contents(load(tmp_path))
    put(tmp_path, "b_spironolactone", "rel_live_0003_candidate",
        edit=lambda records, evidence, manifest: records["records"][0].update(record_id="REL-LIVE-0004"))
    store = load(tmp_path)
    assert contents(store) == before  # neither its record nor its chunk loads
    assert rejection(store, "v2/b_spironolactone") == [
        "v2/b_spironolactone repeats IDs already loaded from another dataset: REL-LIVE-0004 (in v2/a_warfarin)"]


def test_the_root_dataset_takes_precedence_over_a_folder_with_the_same_ids(tmp_path):
    put(tmp_path, None, "food_0001_candidate")
    put(tmp_path, "a_food_copy", "food_0001_candidate")  # sorts first among folders; the root is read before all
    store = load(tmp_path)
    assert [e["dataset"] for e in store.evidence] == ["v2"]
    assert rejection(store, "v2/a_food_copy")


# Test G: a bad dataset after a good one.
@pytest.mark.parametrize("bad", ["tampered text", "manifest hash", "approval"])
def test_a_bad_dataset_does_not_affect_a_good_one(tmp_path, bad):
    put(tmp_path, "a_food", "food_0001_candidate")
    before = contents(load(tmp_path))
    if bad == "tampered text":  # text no longer matches its content hash
        put(tmp_path, "b_warfarin", "rel_live_0004_candidate",
            edit=lambda r, ev, m: ev[0].update(text=ev[0]["text"] + " Never combine them."))
    else:
        put(tmp_path, "b_warfarin", "rel_live_0004_candidate", approval={"approved_by": "", "approved_at": ""}
            if bad == "approval" else None)
        if bad == "manifest hash":
            path = tmp_path / "v2" / "b_warfarin" / NAMES[2]
            path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), "evidence_sha256": "0" * 64}),
                            encoding="utf-8")
    store = load(tmp_path)
    assert contents(store) == before
    expected = {"tampered text": "v2/b_warfarin: 0 approved record(s), 0 evidence chunk(s) loaded",
                "manifest hash": "v2/b_warfarin: LIVE_RELATIONSHIP_RECORDS_V2 evidence file does not match",
                "approval": "v2/b_warfarin: LIVE_RELATIONSHIP_RECORDS_V2 approval is missing approved_by"}[bad]
    assert expected in store.reason, store.reason


# Missing manifest: every discovered folder is loaded or has a reason.
@pytest.mark.parametrize("contents_of_b", ["empty", "data files only"])
def test_a_folder_without_a_manifest_is_reported_and_loads_nothing(tmp_path, contents_of_b):
    put(tmp_path, "a_food", "food_0001_candidate")
    before = contents(load(tmp_path))
    put(tmp_path, "b_warfarin", "rel_live_0004_candidate")
    (tmp_path / "v2" / "b_warfarin" / NAMES[2]).unlink()
    if contents_of_b == "empty":
        for f in (tmp_path / "v2" / "b_warfarin").iterdir():
            f.unlink()
    store = load(tmp_path)
    assert contents(store) == before
    why = "v2/b_warfarin has no LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json, so nothing in it was loaded"
    assert rejection(store, "v2/b_warfarin") == [why] and why in store.reason
    assert "hash" not in why and "approv" not in why  # no misleading approval or hash error


def test_only_a_folder_without_a_manifest_still_reports_it(tmp_path):
    (tmp_path / "v2" / "typo").mkdir(parents=True)
    store = load(tmp_path)
    assert ids(store) == ([], []) and rejection(store, "v2/typo")


# Record-level rejections name their dataset.
def test_record_rejections_in_two_datasets_name_each_dataset(tmp_path):
    put(tmp_path, "rel_live_0003", "rel_live_0003_candidate", severity=None)  # UNGRADED
    put(tmp_path, "rel_live_0004", "rel_live_0004_candidate", severity=None)
    put(tmp_path, "z_bad_hash", "rel_live_0004_candidate", edit=lambda r, ev, m: r["records"][0].update(
        record_id="REL-TEST-HASH", source_content_hash="0" * 64))
    store = load(tmp_path)
    assert ids(store) == ([], [])
    ungraded = "severity UNGRADED is not one of ['CONTRAINDICATED', 'MAJOR', 'MINOR', 'MODERATE', 'NONE']"
    assert set(store.rejected) >= {
        ("REL-LIVE-0003", f"v2/rel_live_0003: {ungraded}"), ("REL-LIVE-0004", f"v2/rel_live_0004: {ungraded}"),
        ("REL-TEST-HASH", "v2/z_bad_hash: source content hash does not match the corpus chunk")}


# Test J: restart.
def test_loading_is_deterministic_across_restarts(tmp_path):
    for folder in ("rel_live_0004", "food_0001", "rel_live_0003"):
        put(tmp_path, folder, f"{folder}_candidate")
    put(tmp_path, "z_food_copy", "food_0001_candidate")  # rejected the same way every time
    first, second = load(tmp_path), load(tmp_path)
    assert contents(first) == contents(second)
    assert (first.status, first.reason, first.rejected) == (second.status, second.reason, second.rejected)


def test_all_datasets_reach_retrieval_and_each_links_to_its_own_source(tmp_path, monkeypatch):
    for folder in ("rel_live_0004", "food_0001", "rel_live_0003"):
        put(tmp_path, folder, f"{folder}_candidate")
    for name in ("LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json", "LIVE_RELATIONSHIP_RECORDS_V1.json"):
        shutil.copyfile(LIVE_DIR / name, tmp_path / name)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.retrieval_info["relationship_evidence_chunks"] == [FOOD_CHUNK, SPIRO_CHUNK, WARFARIN_CHUNK]
    # Two lisinopril sections from one label share its URL and stay verified; each links to its own label.
    assert state.verified_source_links == {e["chunk_id"]: e["source_identity"]["canonical_url"]
                                           for e in state.relationship_store.evidence}


def test_the_live_folder_holds_no_v2_dataset():
    assert not (LIVE_DIR / "v2").exists()
    assert not (LIVE_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").exists()
