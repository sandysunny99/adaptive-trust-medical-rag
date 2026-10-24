"""V2 relationship records with their own versioned evidence file.

A V2 record may cite a chunk of LIVE_RELATIONSHIP_EVIDENCE_V2 (for example exact label text) so
a source can be added without changing the frozen live corpus. Nothing loads unless the V2
manifest is APPROVED by a named person and matches the SHA-256 of both files; an evidence
chunk is retrievable only when an accepted record cites it; and it then passes the same
provenance-hash, trust, eligibility and claim-verification gates as a corpus chunk.

The evidence chunk and records here are synthetic test fixtures in a temporary directory; the
pending REL-LIVE-0002 candidate is not used and stays unapproved.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import _lazy_init_models
from adaptive_trust_medical_rag.services.live_relationships import (
    RELATIONSHIP_DATASET,
    RELATIONSHIP_DATASET_V2,
    live_risk_tier,
    load_relationship_store,
)
from test_live_risk_and_eligibility import CORPUS, RXCUI, corpus_chunk, meds, run, sha

ROOT = Path(__file__).resolve().parents[2]
CHUNK_ID = "TEST-V2-LABEL-SECTION-4.5"
TEXT = ("Concomitant administration of clarithromycin tablets with simvastatin is contraindicated "
        "due to the increased risk of myopathy, including rhabdomyolysis.")
CLAIM = "Simvastatin with clarithromycin is contraindicated [Source 1]."
PAIR = [RXCUI["simvastatin"], RXCUI["clarithromycin"]]


def evidence(**overrides) -> dict:
    text = overrides.pop("text", TEXT)
    item = {
        "chunk_id": CHUNK_ID,
        "document_id": "TEST-SPL-V2",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00000000-0000-0000-0000-000000000000",
        "source_type": "DAILYMED",
        "text": text,
        "content_hash": sha(text),
        "authority": 0.95,
        "freshness": 0.9,
        # Test-only reviewed wording: a pair claim is released only up to its source's reviewed action.
        "supported_claims": [{"text": text, "action": "AVOID"}],
        "embedding": [0.0] * 383 + [1.0],
        "provenance": {"source": "DAILYMED", "chunk_id": CHUNK_ID, "content_hash": sha(text)},
        "source_identity": {
            "provider": "DAILYMED",
            "external_id": "00000000-0000-0000-0000-000000000000",
            "canonical_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00000000-0000-0000-0000-000000000000",
            "title": "TEST LABEL (synthetic fixture)",
            "source_version": "1",
            "captured_at": "2026-10-15T00:00:00Z",
            "capture_sha256": "0" * 64,
            "verification_method": "synthetic test fixture",
        },
    }
    item.update(overrides)
    return item


def v2_record(**overrides) -> dict:
    base = {
        "record_id": "TEST-REL-V2-1",
        "subject": {"name": "simvastatin", "rxcui": RXCUI["simvastatin"]},
        "object": {"name": "clarithromycin", "rxcui": RXCUI["clarithromycin"]},
        "predicate": "CONTRAINDICATION",
        "direction": "BIDIRECTIONAL",
        "severity": "CONTRAINDICATED",
        "source_chunk_id": CHUNK_ID,
        "source_content_hash": sha(TEXT),
        "evidence_span": TEXT,
    }
    base.update(overrides)
    return base


def write_v2(tmp_path: Path, records=None, chunks=None, *, status="APPROVED", approved_by="Test reviewer",
             approved_at="2026-10-15", records_hash=None, evidence_hash=None):
    records_raw = json.dumps({"dataset_version": RELATIONSHIP_DATASET_V2,
                              "records": [v2_record()] if records is None else records}, indent=2).encode("utf-8")
    evidence_raw = json.dumps([evidence()] if chunks is None else chunks, indent=2).encode("utf-8")
    (tmp_path / f"{RELATIONSHIP_DATASET_V2}.json").write_bytes(records_raw)
    (tmp_path / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(evidence_raw)
    manifest = {
        "dataset_version": RELATIONSHIP_DATASET_V2,
        "records_file": f"{RELATIONSHIP_DATASET_V2}.json",
        "records_sha256": records_hash or hashlib.sha256(records_raw).hexdigest(),
        "evidence_file": "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
        "evidence_sha256": evidence_hash or hashlib.sha256(evidence_raw).hexdigest(),
        "status": status,
        "approval": {"approved_by": approved_by, "approved_at": approved_at} if approved_by else None,
    }
    (tmp_path / f"{RELATIONSHIP_DATASET_V2}_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return load_relationship_store(CORPUS, directory=str(tmp_path))


def evidence_candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item["document_url"], source_authority=item["authority"],
        metadata={"provenance": item["provenance"], "source_type": item["source_type"],
                  "freshness_score": item["freshness"], "supported_claims": item.get("supported_claims")},
    ))


def loads_nothing(store) -> bool:
    return store.records == () and store.evidence == ()


# ── The approved path supports a correctly grounded claim ───────────────────

def test_an_approved_v2_record_loads_with_the_evidence_it_cites(tmp_path):
    store = write_v2(tmp_path)
    assert [r.record_id for r in store.records] == ["TEST-REL-V2-1"]
    assert [c["chunk_id"] for c in store.evidence] == [CHUNK_ID]
    assert live_risk_tier(meds("simvastatin", "clarithromycin"), store)[0] == "R3"


def test_the_approved_v2_evidence_supports_the_contraindication_claim(tmp_path):
    store = write_v2(tmp_path)
    kind, data, trust, _ = run([evidence_candidate(store.evidence[0])], store=store)
    assert (trust["risk_class"], trust["threshold"], trust["is_eligible"]) == ("R3", 0.75, True)
    assert kind == "answer", data
    (claim,) = data["claims"]
    assert (claim["canonical_identity_status"], claim["support_state"]) == ("MATCH", "SUPPORTED")


def test_the_bidirectional_record_supports_either_drug_order(tmp_path):
    store = write_v2(tmp_path)
    kind, data, _, _ = run([evidence_candidate(store.evidence[0])], store=store,
                           answer={"conclusion": "Clarithromycin with simvastatin is contraindicated [Source 1]."})
    assert kind == "answer", data
    assert data["claims"][0]["support_state"] == "SUPPORTED"


def test_approved_v2_evidence_joins_retrieval_without_changing_the_frozen_corpus(tmp_path, monkeypatch):
    write_v2(tmp_path)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.retrieval_info["relationship_evidence_chunks"] == [CHUNK_ID]
    assert state.retrieval_info["chunk_count"] == len(CORPUS) + 1
    found = state.retrieval_engine.retrieve("simvastatin clarithromycin contraindicated",
                                            query_drugs=["simvastatin", "clarithromycin"], top_k=20)
    assert CHUNK_ID in {sc.candidate.chunk_id for sc in found}
    assert CHUNK_ID not in {item["chunk_id"] for item in CORPUS}


def test_approved_v2_evidence_with_a_source_identity_record_is_identity_verified(tmp_path, monkeypatch):
    write_v2(tmp_path)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.verified_source_links == {CHUNK_ID: evidence()["document_url"]}


def test_approved_v2_evidence_without_a_source_identity_record_is_not_verified(tmp_path, monkeypatch):
    item = evidence()
    del item["source_identity"]
    write_v2(tmp_path, chunks=[item])
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.verified_source_links == {}


# ── Everything short of an approved, intact dataset fails closed ─────────────

def test_a_pending_v2_dataset_is_not_retrievable(tmp_path, monkeypatch):
    write_v2(tmp_path, status="CANDIDATE_PENDING_RESEARCHER_APPROVAL", approved_by=None)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert "relationship_evidence_chunks" not in state.retrieval_info
    assert loads_nothing(state.relationship_store)
    assert f"{RELATIONSHIP_DATASET_V2} is CANDIDATE_PENDING_RESEARCHER_APPROVAL, not approved" in state.relationship_store.reason


@pytest.mark.parametrize("kwargs", [
    {"status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL", "approved_by": None},
    {"status": "APPROVED", "approved_by": None},
    {"status": "APPROVED", "approved_at": ""},
    {"status": "PENDING", "approved_by": "Test reviewer"},
])
def test_v2_without_a_named_approval_loads_nothing(tmp_path, kwargs):
    assert loads_nothing(write_v2(tmp_path, **kwargs))


@pytest.mark.parametrize("which", ["records_hash", "evidence_hash"])
def test_a_v2_file_that_does_not_match_its_manifest_loads_nothing(tmp_path, which):
    store = write_v2(tmp_path, **{which: "0" * 64})
    assert loads_nothing(store)
    assert f"{RELATIONSHIP_DATASET_V2} {which.split('_')[0]} file does not match the manifest SHA-256" in store.reason


@pytest.mark.parametrize(("chunk", "why"), [
    (evidence(content_hash="0" * 64), "content hash"),
    (evidence(provenance={"source": "DAILYMED", "content_hash": "0" * 64}), "provenance"),
    (evidence(provenance={"content_hash": sha(TEXT)}), "provenance"),
    (evidence(document_url="http://dailymed.nlm.nih.gov/x"), "https"),
    (evidence(embedding=[0.0] * 10), "embedding"),
    (evidence(authority=None), "missing"),
    (evidence(chunk_id="DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01"), "frozen corpus"),
])
def test_an_invalid_evidence_chunk_is_rejected_with_its_records(tmp_path, chunk, why):
    record = v2_record(source_chunk_id=chunk["chunk_id"]) if chunk["chunk_id"] != CHUNK_ID else v2_record()
    store = write_v2(tmp_path, records=[record], chunks=[chunk])
    assert store.evidence == ()
    assert any(why in reason for _, reason in store.rejected), store.rejected
    if chunk["chunk_id"] == CHUNK_ID:
        assert store.records == ()


def test_an_edited_evidence_text_is_rejected_even_with_a_recomputed_manifest(tmp_path):
    tampered = evidence()
    tampered["text"] = TEXT.replace("contraindicated", "acceptable")
    assert loads_nothing(write_v2(tmp_path, chunks=[tampered]))


def test_a_chunk_no_accepted_record_cites_is_not_retrievable(tmp_path):
    other = evidence(chunk_id="TEST-V2-UNCITED", provenance={"source": "DAILYMED", "content_hash": sha(TEXT)})
    store = write_v2(tmp_path, chunks=[evidence(), other])
    assert [c["chunk_id"] for c in store.evidence] == [CHUNK_ID]


@pytest.mark.parametrize(("overrides", "why"), [
    ({"object": {"name": "erythromycin", "rxcui": "4053"}}, "does not name both medications"),
    ({"predicate": "SAFE_TOGETHER"}, "bounded predicate set"),
    ({"predicate": "INHIBITION", "direction": "BIDIRECTIONAL"}, "directional"),
    ({"direction": "SIDEWAYS"}, "incomplete record"),
    ({"direction": "UNKNOWN"}, "direction is unknown"),
    ({"source_content_hash": "0" * 64}, "content hash"),
    ({"evidence_span": "Simvastatin and clarithromycin may be taken together."}, "not verbatim"),
])
def test_an_invalid_v2_record_is_rejected(tmp_path, overrides, why):
    store = write_v2(tmp_path, records=[v2_record(**overrides)])
    assert loads_nothing(store)
    assert any(why in reason for _, reason in store.rejected), store.rejected


def test_a_claim_with_another_predicate_does_not_match_the_v2_record(tmp_path):
    store = write_v2(tmp_path)
    kind, data, _, _ = run([evidence_candidate(store.evidence[0])], store=store,
                           answer={"conclusion": "Simvastatin inhibits clarithromycin [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "MISMATCH"


def test_a_query_for_another_pair_gets_no_identity_from_the_v2_record(tmp_path):
    store = write_v2(tmp_path)
    assert store.identity_for_chunk(CHUNK_ID, TEXT, [RXCUI["simvastatin"], RXCUI["metformin"]]) is None
    assert store.identity_for_chunk(CHUNK_ID, TEXT, PAIR) is not None


def test_a_v1_record_cannot_cite_v2_evidence(tmp_path):
    write_v2(tmp_path)
    raw = json.dumps({"dataset_version": RELATIONSHIP_DATASET, "records": [v2_record(record_id="V1")]}).encode("utf-8")
    (tmp_path / f"{RELATIONSHIP_DATASET}.json").write_bytes(raw)
    (tmp_path / f"{RELATIONSHIP_DATASET}_MANIFEST.json").write_text(json.dumps({
        "records_file": f"{RELATIONSHIP_DATASET}.json", "records_sha256": hashlib.sha256(raw).hexdigest(),
        "status": "APPROVED", "approval": {"approved_by": "Test reviewer", "approved_at": "2026-10-15"}}),
        encoding="utf-8")
    store = load_relationship_store(CORPUS, directory=str(tmp_path))
    assert [r.record_id for r in store.records] == ["TEST-REL-V2-1"]
    assert ("V1", f"source chunk {CHUNK_ID} is not in the live corpus") in store.rejected


def test_the_retrieval_time_hash_check_still_blocks_altered_v2_text(tmp_path):
    store = write_v2(tmp_path)
    item = dict(store.evidence[0], text=TEXT + " Updated.")
    kind, data, _, llm = run([evidence_candidate(item)], store=store)
    assert kind == "abstention" and llm.calls == 0
    assert "integrity" in data["reason"]


def test_without_a_v2_manifest_the_store_is_v1_alone(tmp_path):
    assert load_relationship_store(CORPUS, directory=str(tmp_path)).reason == \
        f"{RELATIONSHIP_DATASET} manifest not found"


def test_the_shipped_data_has_no_v2_dataset():
    assert not os.path.exists(os.path.join(live_relationships.RELATIONSHIP_DIR, f"{RELATIONSHIP_DATASET_V2}_MANIFEST.json"))
    assert load_relationship_store(CORPUS).evidence == ()


def test_a_v2_mixed_with_a_good_chunk_and_a_stale_one_keeps_only_the_good_one(tmp_path):
    stale = evidence(chunk_id="TEST-V2-STALE", content_hash="0" * 64)
    store = write_v2(tmp_path, records=[v2_record(), v2_record(record_id="STALE", source_chunk_id="TEST-V2-STALE")],
                     chunks=[evidence(), stale])
    assert [r.record_id for r in store.records] == ["TEST-REL-V2-1"]
    assert [c["chunk_id"] for c in store.evidence] == [CHUNK_ID]


def test_unrelated_v2_evidence_is_still_excluded_before_scoring(tmp_path):
    store = write_v2(tmp_path)
    _, _, trust, _ = run([evidence_candidate(store.evidence[0]), corpus_chunk("DAILYMED-SPL-WARFARIN-001-CHUNK-01")],
                         store=store)
    assert trust["unrelated_excluded"] == 1
