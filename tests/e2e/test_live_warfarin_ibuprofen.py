"""Warfarin + ibuprofen through the real live pipeline: placeholders, the REL-LIVE-0004 candidate, tampering.

REL-LIVE-0004 is real DailyMed text (warfarin SPL v8, section 7.3), built by
scripts/build_rel_live_0004_candidate.py and kept pending. Positive paths approve a copy only inside
tmp_path, with a test-only severity; the shipped candidate stays pending and UNGRADED.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService, _lazy_init_models
from adaptive_trust_medical_rag.services.live_source_links import shared_urls
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

ROOT = Path(__file__).resolve().parents[2]
REL_DIR = ROOT / "data" / "live_medical" / "relationships"
FIXTURE = ROOT / "tests" / "fixtures" / "rel_live_0004_candidate"
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
RXCUI = {"warfarin": "11289", "ibuprofen": "5640"}
LABEL = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=884cdbf6-0a52-4126-8e14-b0d7c9367e33"
CLAIM = ("Warfarin interacts with ibuprofen and can increase the risk of bleeding; patients should be "
         "closely monitored [Source 1].")
TEST_ONLY_SEVERITY = "MODERATE"  # lets the fixture load; not a clinical grade


# Fixture assumption (2026-10-26 audit, LIVE_TRUST_FACTORS_V2): the vector channel returned this chunk
# at cosine 0.6; the real lisinopril label section 7.1 measured 0.57 for its pair query. Without a
# measured relevance a chunk scores below the R2 threshold, which these tests do not exercise.
FIXTURE_RELEVANCE = 0.6


def as_candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item.get("document_url", ""), source_authority=item.get("authority", 0.5),
        metadata={"provenance": item.get("provenance", {}), "source_type": item.get("source_type"),
                  "freshness_score": item.get("freshness", 0.8), "source_identity": item.get("source_identity"),
                  "supported_claims": item.get("supported_claims")},
    ), vector_similarity=FIXTURE_RELEVANCE)


class Retrieval:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query, query_drugs, top_k=20):
        return self.chunks


class Normalizer:
    async def normalize_batch(self, names):
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI[n.lower()], brand_name=None,
                                formulation=None, confidence=1.0, source="TEST") for n in names]


class LLM:
    def __init__(self, answer):
        self.content, self.calls = json.dumps(answer), 0

    async def generate_structured(self, prompt, response_format, provider_name=None):
        self.calls += 1
        return SimpleNamespace(content=self.content, provider="mock", model="mock-llm")


@pytest.fixture(scope="module")
def verifier():
    return ClaimVerifierV2()


def run(state):
    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute("req-wi", ["Warfarin", "Ibuprofen"], None, 0)]

    events = asyncio.run(collect())
    terminal = [e for e in events if e["event"] in ("answer", "abstention", "error")]
    assert len(terminal) == 1
    trust = next((e["data"] for e in events if e["event"] == "trust"), {})
    generated = any(e["event"] == "stage_update" and e["data"].get("stage") == "generating" for e in events)
    return terminal[0]["event"], terminal[0]["data"], trust, generated


def stage(tmp_path, *, approve=True, severity=TEST_ONLY_SEVERITY, tamper=None, fixture=FIXTURE, dest=None,
          edit=None):
    """Copy REL-LIVE-0004 (or another candidate) into tmp_path or dest (approved there only), optionally tampered.

    ``edit(records, evidence, manifest)`` changes the copy before its hashes are computed.
    """
    dest = dest or tmp_path
    dest.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((fixture / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").read_text(encoding="utf-8"))
    records = json.loads((fixture / "LIVE_RELATIONSHIP_RECORDS_V2.json").read_text(encoding="utf-8"))
    manifest = json.loads((fixture / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL" and manifest["approval"] is None
    for record in records["records"]:
        if severity:
            record["severity"] = severity
    if tamper:
        tamper(evidence[0])
    if edit:
        edit(records, evidence, manifest)
    ev_raw = (json.dumps(evidence) + "\n").encode("utf-8")
    rec_raw = (json.dumps(records) + "\n").encode("utf-8")
    (dest / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(ev_raw)
    (dest / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(rec_raw)
    manifest.update(records_sha256=hashlib.sha256(rec_raw).hexdigest(), evidence_sha256=hashlib.sha256(ev_raw).hexdigest())
    if approve:
        manifest.update(status="APPROVED", approval={"approved_by": "Test fixture", "approved_at": "2026-10-22"})
    (dest / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name in ("LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json", "LIVE_RELATIONSHIP_RECORDS_V1.json"):
        shutil.copyfile(REL_DIR / name, tmp_path / name)


def load(tmp_path, monkeypatch):
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    return state


def pipeline_state(loaded, chunks, answer, verifier):
    return SimpleNamespace(
        drug_normalizer=Normalizer(), retrieval_engine=Retrieval(chunks), llm_backend=LLM(answer),
        claim_verifier=verifier, model_init_errors={}, relationship_store=loaded.relationship_store,
        shared_source_urls=loaded.shared_source_urls, verified_source_links=loaded.verified_source_links)


# Scenario 1: the frozen corpus, as in the screenshots.
def test_the_frozen_corpus_rejects_both_placeholders_and_never_calls_the_model(verifier):
    llm = LLM({"conclusion": CLAIM})
    state = SimpleNamespace(drug_normalizer=Normalizer(), retrieval_engine=Retrieval([as_candidate(i) for i in CORPUS]),
                            llm_backend=llm, claim_verifier=verifier, model_init_errors={},
                            shared_source_urls=shared_urls(CORPUS), verified_source_links={})
    kind, data, trust, generated = run(state)
    assert kind == "abstention" and llm.calls == 0 and not generated
    assert (trust["unrelated_excluded"], trust["unverified_source_excluded"]) == (12, 2)
    assert {e["document_id"]: e["source_link_status"] for e in data["excluded_sources"]} == {
        "SPL-WARFARIN-001": "PLACEHOLDER", "SPL-IBUPROFEN-001": "PLACEHOLDER"}
    assert trust["overall_score"] is None


# The candidate as shipped.
def test_the_shipped_candidate_is_real_label_text_and_loads_nothing(tmp_path, monkeypatch):
    (item,) = json.loads((FIXTURE / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").read_text(encoding="utf-8"))
    assert item["source_identity"]["canonical_url"] == LABEL and item["text"].startswith("7.3 Drugs that Increase Bleeding Risk")
    assert "ibuprofen" in item["text"] and "closely monitor patients" in item["text"]
    stage(tmp_path, approve=False, severity=None)
    assert load(tmp_path, monkeypatch).relationship_store.records == ()


def test_the_ungraded_record_is_rejected_even_if_approved(tmp_path, monkeypatch):
    stage(tmp_path, severity=None)
    store = load(tmp_path, monkeypatch).relationship_store
    assert store.records == () and store.evidence == ()


# Scenario 2: verified source and approved record (temporary).
def test_relationship_verification_runs_and_the_answer_is_released(tmp_path, monkeypatch, verifier):
    stage(tmp_path)
    loaded = load(tmp_path, monkeypatch)
    (item,) = loaded.relationship_store.evidence
    kind, data, trust, generated = run(pipeline_state(loaded, [as_candidate(item)], {"conclusion": CLAIM}, verifier))
    assert generated and kind == "answer", data.get("reason")
    (claim,) = data["claims"]
    assert (claim["support_state"], claim["canonical_identity_status"]) == ("SUPPORTED", "MATCH")
    assert data["evidence"][0]["url"] == LABEL and data["evidence"][0]["source_identity_status"] == "VERIFIED"


def test_an_overstated_pair_claim_is_withheld(tmp_path, monkeypatch, verifier):
    stage(tmp_path)
    loaded = load(tmp_path, monkeypatch)
    (item,) = loaded.relationship_store.evidence
    answer = {"conclusion": "Warfarin interacts with ibuprofen, so never combine them [Source 1]."}
    kind, data, _, _ = run(pipeline_state(loaded, [as_candidate(item)], answer, verifier))
    assert kind == "abstention" and data["claims"][0]["support_state"] != "SUPPORTED"


def test_with_a_second_dataset_loaded_the_gates_still_pick_only_the_warfarin_evidence(tmp_path, monkeypatch, verifier):
    stage(tmp_path, dest=tmp_path / "v2" / "rel_live_0004")
    stage(tmp_path, fixture=FIXTURE.parent / "food_0001_candidate", dest=tmp_path / "v2" / "food_0001")
    loaded = load(tmp_path, monkeypatch)
    chunks = [as_candidate(item) for item in loaded.relationship_store.evidence]  # both datasets retrieved
    assert len(chunks) == 2
    kind, data, trust, generated = run(pipeline_state(loaded, chunks, {"conclusion": CLAIM}, verifier))
    assert generated and kind == "answer", data.get("reason")
    assert trust["unrelated_excluded"] == 1  # the lisinopril food passage names neither drug
    assert [(e["url"], e["source_identity_status"]) for e in data["evidence"]] == [(LABEL, "VERIFIED")]
    (claim,) = data["claims"]
    assert (claim["support_state"], claim["canonical_identity_status"]) == ("SUPPORTED", "MATCH")


# The same text from two verified sources (different chunk IDs and URLs) in two datasets.
# SYNTHETIC: a made-up set ID in DailyMed form, test-only, so the copy is a distinct verified source.
SYN_SETID = "0000000b-0000-4000-8000-00000000000b"
SYN_URL = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={SYN_SETID}"
SYN_CHUNK = "TEST-SYNTHETIC-B-SEC-7.3"


def as_second_source(with_record: bool):
    def edit(records, evidence, manifest):
        e = evidence[0]
        e.update(chunk_id=SYN_CHUNK, document_id=f"DAILYMED-SPL-{SYN_SETID}", document_url=SYN_URL)
        e["provenance"].update(chunk_id=SYN_CHUNK, document_id=e["document_id"])
        e["source_identity"].update(external_id=SYN_SETID, canonical_url=SYN_URL)
        if with_record:
            records["records"][0].update(record_id="REL-TEST-B", source_chunk_id=SYN_CHUNK)
        else:
            records["records"] = []
            manifest["standalone_evidence_chunks"] = [SYN_CHUNK]
    return edit


def run_same_text(tmp_path, monkeypatch, verifier, *, b_first: bool, b_has_record: bool):
    stage(tmp_path, dest=tmp_path / "v2" / "a_warfarin")
    stage(tmp_path, dest=tmp_path / "v2" / "b_same_text", edit=as_second_source(b_has_record))
    loaded = load(tmp_path, monkeypatch)
    assert sorted(loaded.verified_source_links.values()) == sorted([LABEL, SYN_URL])  # both verified
    by_id = {e["chunk_id"]: e for e in loaded.relationship_store.evidence}
    assert by_id[CHUNK_ID]["content_hash"] == by_id[SYN_CHUNK]["content_hash"]  # same text, own identity
    assert (by_id[CHUNK_ID]["dataset"], by_id[SYN_CHUNK]["dataset"]) == ("v2/a_warfarin", "v2/b_same_text")
    order = [by_id[SYN_CHUNK], by_id[CHUNK_ID]] if b_first else [by_id[CHUNK_ID], by_id[SYN_CHUNK]]
    events = []

    async def collect():
        state = pipeline_state(loaded, [as_candidate(i) for i in order], {"conclusion": CLAIM}, verifier)
        events.extend([e async for e in LiveMedicalRAGService(state).execute(
            "req-same", ["Warfarin", "Ibuprofen"], None, 0)])

    asyncio.run(collect())
    (terminal,) = [e for e in events if e["event"] in ("answer", "abstention", "error")]
    return terminal["event"], terminal["data"], json.dumps(events)


CHUNK_ID = "DAILYMED-884CDBF6-SPL-V8-SEC-7.3"


@pytest.mark.parametrize("b_first", [False, True])
def test_the_same_text_from_two_sources_cites_only_the_copy_that_was_used(tmp_path, monkeypatch, verifier, b_first):
    kind, data, stream = run_same_text(tmp_path, monkeypatch, verifier, b_first=b_first, b_has_record=True)
    used, dropped = (SYN_URL, LABEL) if b_first else (LABEL, SYN_URL)
    assert kind == "answer", data.get("reason")
    assert [(e["url"], e["source_identity_status"]) for e in data["evidence"]] == [(used, "VERIFIED")]
    (claim,) = data["claims"]
    assert (claim["support_state"], claim["canonical_identity_status"]) == ("SUPPORTED", "MATCH")
    assert dropped not in stream  # the copy not used is never cited or implied, in any event
    assert "dataset_approval" not in stream  # loader provenance stays internal


def test_a_kept_copy_without_its_own_record_is_not_lent_the_other_copys_record(tmp_path, monkeypatch, verifier):
    # B ranks first but has no record; A's record names A's chunk only, so B gets no relationship identity.
    kind, data, _ = run_same_text(tmp_path, monkeypatch, verifier, b_first=True, b_has_record=False)
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "UNAVAILABLE"
    assert LABEL not in json.dumps(data)


def test_the_same_text_result_is_the_same_after_a_restart(tmp_path, monkeypatch, verifier):
    runs = []
    for attempt in ("first", "second"):
        root = tmp_path / attempt
        root.mkdir()
        kind, data, _ = run_same_text(root, monkeypatch, verifier, b_first=True, b_has_record=True)
        runs.append((kind, [e["url"] for e in data["evidence"]], [c["support_state"] for c in data["claims"]]))
    assert runs[0] == runs[1] == ("answer", [SYN_URL], ["SUPPORTED"])


# Scenario 3: valid source, no relationship record.
def test_a_verified_source_without_a_relationship_record_abstains(tmp_path, monkeypatch, verifier):
    stage(tmp_path)
    loaded = load(tmp_path, monkeypatch)
    (item,) = loaded.relationship_store.evidence
    loaded.relationship_store = live_relationships.RelationshipStore()  # source verified, no record
    kind, data, _, generated = run(pipeline_state(loaded, [as_candidate(item)], {"conclusion": CLAIM}, verifier))
    assert generated and kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "UNAVAILABLE"


# Scenario 4: manipulated provenance.
@pytest.mark.parametrize("tamper", [
    lambda e: e.update(text=e["text"] + " Avoid this combination."),                      # text no longer matches its hash
    lambda e: e["source_identity"].update(external_id="00000000-0000-0000-0000-000000000000"),  # wrong set ID
    lambda e: e.update(document_url=e["document_url"].replace("884cdbf6", "example-")),   # placeholder URL
])
def test_tampered_evidence_fails_closed(tmp_path, monkeypatch, tamper):
    stage(tmp_path, tamper=tamper)
    loaded = load(tmp_path, monkeypatch)
    # Either the chunk is rejected outright (hash), or it loads but is never identity-verified.
    assert loaded.relationship_store.evidence == () or loaded.verified_source_links == {}
