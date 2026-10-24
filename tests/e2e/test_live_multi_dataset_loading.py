"""V2 relationship datasets, each in its own folder (relationships/v2/<dataset>/), with no dataset present.

No dataset loads nothing, a folder without a manifest is reported, and the live folder ships no V2 dataset.
Tests that load datasets use candidate evidence still pending researcher approval as their fixtures, so they
are kept outside version control until it is reviewed. The live folder is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

from adaptive_trust_medical_rag.services.live_relationships import load_relationship_store

ROOT = Path(__file__).resolve().parents[2]
LIVE_DIR = ROOT / "data" / "live_medical" / "relationships"
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))


def load(root: Path):
    return load_relationship_store(CORPUS, directory=str(root))


def ids(store):
    return sorted(r.record_id for r in store.records), sorted(e["chunk_id"] for e in store.evidence)


def rejection(store, label):
    return [why for who, why in store.rejected if who == label]


# Test H: nothing, pending, ungraded, incomplete approval.
def test_no_datasets_load_nothing(tmp_path):
    assert ids(load(tmp_path)) == ([], [])


def test_only_a_folder_without_a_manifest_still_reports_it(tmp_path):
    (tmp_path / "v2" / "typo").mkdir(parents=True)
    store = load(tmp_path)
    assert ids(store) == ([], []) and rejection(store, "v2/typo")


def test_the_live_folder_holds_no_v2_dataset():
    assert not (LIVE_DIR / "v2").exists()
    assert not (LIVE_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").exists()
