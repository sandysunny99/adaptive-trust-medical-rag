"""Evidence provenance gates for the lisinopril + spironolactone regression.

Source identity is a hard gate separate from every score: a chunk is evidence only when its source
identity is verified, and only an approved V2 evidence record with a complete source identity
record makes it so. Placeholder DailyMed links, the PubMed ID shared by unrelated documents and
unverified links are excluded before generation, whatever their authority or trust score.

Test J copies the REL-LIVE-0003 candidate (real DailyMed text, built by
scripts/build_rel_live_0003_candidate.py) into a temporary directory and approves it there, so
the shipped candidate stays unapproved. The claim verifier is the real ClaimVerifierV2.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService, _lazy_init_models
from adaptive_trust_medical_rag.services.live_source_links import (
    check_source_identity,
    shared_urls,
    source_identity_status,
    source_link,
)
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

ROOT = Path(__file__).resolve().parents[2]
REL_DIR = ROOT / "data" / "live_medical" / "relationships"
# The pending candidate is kept with its audit run, outside the live data folder (as REL-LIVE-0002 is).
CANDIDATE_DIR = ROOT / "tests" / "fixtures" / "rel_live_0003_candidate"
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
BY_ID = {item["chunk_id"]: item for item in CORPUS}
RXCUI = {"lisinopril": "29046", "spironolactone": "9997"}
CLAIM = "Lisinopril interacts with spironolactone and can increase the risk of hyperkalemia [Source 1]."


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item.get("document_url", ""), source_authority=item.get("authority", 0.5),
        metadata={"provenance": item.get("provenance", {}), "source_type": item.get("source_type"),
                  "freshness_score": item.get("freshness", 0.8), "source_identity": item.get("source_identity")},
    ))


class StubRetrieval:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query, query_drugs, top_k=20):
        return self.chunks


class OfflineNormalizer:
    async def normalize_batch(self, names):
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI[n.lower()], brand_name=None,
                                formulation=None, confidence=1.0, source="TEST") for n in names]


class CountingLLM:
    def __init__(self, answer: dict | None = None, error: Exception | None = None):
        self.content = json.dumps(answer or {"conclusion": CLAIM})
        self.error = error
        self.calls = 0

    async def generate_structured(self, prompt, response_format, provider_name=None):
        self.calls += 1
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content, provider="mock", model="mock-llm")


@pytest.fixture(scope="module")
def verifier():
    return ClaimVerifierV2()


def run(state: SimpleNamespace, drugs=("Lisinopril", "Spironolactone")):
    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute("req-prov", list(drugs), None, 0)]

    events = asyncio.run(collect())
    terminal = [e for e in events if e["event"] in ("answer", "abstention", "error")]
    assert len(terminal) == 1, [e["event"] for e in events]
    trust = next((e["data"] for e in events if e["event"] == "trust"), None)
    return terminal[0]["event"], terminal[0]["data"], trust, events


def frozen_state(chunk_ids, verifier, llm=None):
    """The live state over frozen corpus chunks, with the links the application itself computes."""
    return SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval([as_candidate(BY_ID[c]) for c in chunk_ids]),
        llm_backend=llm or CountingLLM(),
        claim_verifier=verifier,
        model_init_errors={},
        shared_source_urls=shared_urls(CORPUS),
        verified_source_links={},  # no frozen chunk has a verified source identity
    )


# A severity chosen only so the fixture can load; it is not a clinical grade of this interaction.
TEST_ONLY_SEVERITY = "MODERATE"


def stage_candidate(tmp_path, *, severity: str | None = TEST_ONLY_SEVERITY):
    """Copy REL-LIVE-0003 into tmp_path and approve it there; the shipped candidate stays pending."""
    shutil.copyfile(CANDIDATE_DIR / "LIVE_RELATIONSHIP_EVIDENCE_V2.json", tmp_path / "LIVE_RELATIONSHIP_EVIDENCE_V2.json")
    records = json.loads((CANDIDATE_DIR / "LIVE_RELATIONSHIP_RECORDS_V2.json").read_text(encoding="utf-8"))
    assert records["records"][0]["severity"] == "UNGRADED"  # the shipped record has no grade
    if severity is not None:
        records["records"][0]["severity"] = severity
    raw = (json.dumps(records, indent=2) + "\n").encode("utf-8")
    (tmp_path / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(raw)
    manifest = json.loads((CANDIDATE_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL"  # the shipped file is not approved
    manifest.update(status="APPROVED", approval={"approved_by": "Test fixture", "approved_at": "2026-10-22"},
                    records_sha256=hashlib.sha256(raw).hexdigest())
    (tmp_path / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    shutil.copyfile(REL_DIR / "LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json", tmp_path / "LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json")
    shutil.copyfile(REL_DIR / "LIVE_RELATIONSHIP_RECORDS_V1.json", tmp_path / "LIVE_RELATIONSHIP_RECORDS_V1.json")


@pytest.fixture
def approved_candidate(tmp_path, monkeypatch):
    """REL-LIVE-0003 as built from DailyMed, approved inside tmp_path with a test-only severity."""
    stage_candidate(tmp_path)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    return state


# ── The shipped state: the candidate loads nothing ───────────────────────────

def test_the_shipped_rel_live_0003_candidate_is_not_loaded(monkeypatch):
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.relationship_store.evidence == ()
    assert not (REL_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").exists()  # not in the live data folder
    assert state.verified_source_links == {}
    manifest = json.loads((CANDIDATE_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL" and manifest["approval"] is None


def test_the_candidate_evidence_is_real_label_text_naming_both_drugs():
    (item,) = json.loads((CANDIDATE_DIR / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").read_text(encoding="utf-8"))
    assert item["content_hash"] == sha(item["text"])
    assert "spironolactone" in item["text"] and "lisinopril" in item["text"]
    assert "can increase the risk of hyperkalemia" in item["text"]
    assert check_source_identity(item) == "verified"
    assert item["source_identity"]["external_id"] == "34ebeea1-6812-4697-84c4-b2ae4f39e55f"


# ── Test K: placeholder DailyMed records ─────────────────────────────────────

@pytest.mark.parametrize("chunk_id", ["DAILYMED-SPL-LISINOPRIL-001-CHUNK-01", "DAILYMED-SPL-LISINOPRIL-002-CHUNK-01"])
def test_a_placeholder_dailymed_record_is_rejected_whatever_its_scores(chunk_id):
    item = BY_ID[chunk_id]
    assert "setid=example-lisinopril" in item["document_url"] and item["authority"] == 0.95
    link = source_link(chunk_id, item["document_url"], shared=shared_urls(CORPUS))
    assert source_identity_status(link["status"]) == "REJECTED_SOURCE_IDENTITY"


def test_a_source_identity_record_cannot_verify_a_placeholder_url():
    item = dict(BY_ID["DAILYMED-SPL-LISINOPRIL-001-CHUNK-01"])
    item["source_identity"] = {"provider": "DAILYMED", "external_id": "example-lisinopril",
                               "canonical_url": item["document_url"], "title": "x", "source_version": "1",
                               "captured_at": "t", "capture_sha256": "0" * 64, "verification_method": "claimed"}
    assert check_source_identity(item) == "source URL is a placeholder"


def test_placeholder_lisinopril_records_never_reach_the_model(verifier):
    llm = CountingLLM()
    kind, data, trust, _ = run(frozen_state(
        ["DAILYMED-SPL-LISINOPRIL-001-CHUNK-01", "DAILYMED-SPL-LISINOPRIL-002-CHUNK-01",
         "PUBMED-PMID-31234567-CHUNK-01"], verifier, llm))
    assert kind == "abstention" and llm.calls == 0
    assert "none has a verified source identity" in data["reason"]
    assert {e["source_identity_status"] for e in data["excluded_sources"]} == {"REJECTED_SOURCE_IDENTITY"}
    assert trust["is_eligible"] is False and trust["overall_score"] is None
    assert trust["score_status"] == "NO_ELIGIBLE_EVIDENCE" and trust["scored_chunks"] == 0
    assert trust["unverified_source_excluded"] == 3
    assert "evidence" not in data


# ── Test L: PMID 31234567 ────────────────────────────────────────────────────
# PubMed esummary, 2026-10-22: PMID 31234567 is "Assessment of the Spatial Distribution of Moisture
# Content in Granular Material Using Electrical Impedance Tomography", Sensors (Basel) 2019. It is
# about neither lisinopril and potassium nor food interactions, the two corpus documents that cite it.

@pytest.mark.parametrize("chunk_id", ["PUBMED-PMID-31234567-CHUNK-01", "PUBMED-PUBMED-31234567-001-CHUNK-01"])
def test_the_pmid_given_to_two_unrelated_documents_identifies_neither(chunk_id):
    item = BY_ID[chunk_id]
    link = source_link(chunk_id, item["document_url"], shared=shared_urls(CORPUS))
    assert link["status"] == "SHARED"
    assert source_identity_status(link["status"]) == "REJECTED_SOURCE_IDENTITY"


def test_a_pubmed_identity_record_must_resolve_its_own_pmid():
    item = {"chunk_id": "c", "source_type": "PUBMED", "document_url": "https://pubmed.ncbi.nlm.nih.gov/31234567",
            "source_identity": {"provider": "PUBMED", "external_id": "99999999",
                                "canonical_url": "https://pubmed.ncbi.nlm.nih.gov/31234567", "title": "x",
                                "source_version": "2019", "captured_at": "t", "capture_sha256": "0" * 64,
                                "verification_method": "esummary"}}
    assert check_source_identity(item) == "PubMed URL does not resolve the recorded PMID"


def test_the_misattributed_food_interaction_record_cannot_ground_food_guidance(verifier):
    llm = CountingLLM({"conclusion": "Take with food.", "food_guidance": [{
        "drug": "Lisinopril", "administration": "oral", "food_relationship": "WITH_FOOD", "timing": "",
        "food_interactions": ["Avoid grapefruit [Source 1]."], "evidence_status": "VERIFIED", "source": "[Source 1]"}]})
    kind, data, _, _ = run(frozen_state(["PUBMED-PUBMED-31234567-001-CHUNK-01", "DAILYMED-SPL-LISINOPRIL-001-CHUNK-01"],
                                        verifier, llm))
    assert kind == "abstention" and llm.calls == 0
    assert "food_guidance" not in data


# ── Test J: authentic evidence for lisinopril + spironolactone ──────────────

def test_the_ungraded_candidate_is_rejected_even_if_its_manifest_were_approved(tmp_path, monkeypatch):
    stage_candidate(tmp_path, severity=None)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    assert state.relationship_store.between([RXCUI["lisinopril"], RXCUI["spironolactone"]]) == []
    assert ("REL-LIVE-0003", "severity UNGRADED is not one of ['CONTRAINDICATED', 'MAJOR', 'MINOR', 'MODERATE', "
            "'NONE']") in state.relationship_store.rejected
    assert state.verified_source_links == {}  # uncited evidence never joins retrieval


def test_approved_label_evidence_is_identity_verified(approved_candidate):
    chunk_id = "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1"
    assert approved_candidate.verified_source_links == {
        chunk_id: "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34ebeea1-6812-4697-84c4-b2ae4f39e55f"}
    (record,) = approved_candidate.relationship_store.between([RXCUI["lisinopril"], RXCUI["spironolactone"]])
    assert (record.record_id, record.predicate, record.direction.value) == ("REL-LIVE-0003", "INTERACTION", "BIDIRECTIONAL")


def test_the_hyperkalemia_interaction_claim_is_supported_by_the_real_label(approved_candidate, verifier):
    evidence = approved_candidate.relationship_store.evidence
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval([as_candidate(e) for e in evidence]
                                       + [as_candidate(BY_ID["DAILYMED-SPL-LISINOPRIL-001-CHUNK-01"])]),
        llm_backend=CountingLLM(), claim_verifier=verifier, model_init_errors={},
        relationship_store=approved_candidate.relationship_store,
        shared_source_urls=approved_candidate.shared_source_urls,
        verified_source_links=approved_candidate.verified_source_links,
    )
    kind, data, trust, _ = run(state)
    # A MODERATE (test-only) record does not raise the tier: only CONTRAINDICATED or MAJOR would.
    assert trust["risk_class"] == "R2" and trust["unverified_source_excluded"] == 1
    (item,) = data["evidence"]
    assert item["source_identity_status"] == "VERIFIED"
    assert item["external_id"] == "34ebeea1-6812-4697-84c4-b2ae4f39e55f"
    assert item["url"] == "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34ebeea1-6812-4697-84c4-b2ae4f39e55f"
    assert item["provenance_status"] == "CONTENT_HASH_MATCHED"
    assert kind == "answer", data.get("reason")
    assert data["claims"][0]["support_state"] == "SUPPORTED"
    assert data["claims"][0]["canonical_identity_status"] == "MATCH"
    assert item["claim_support_status"] == "SUPPORTS_VERIFIED_CLAIM"


# ── Test M: correct source, wrong claim ──────────────────────────────────────

def test_a_fetal_toxicity_section_cannot_support_a_hyperkalemia_claim(verifier):
    fetal = dict(BY_ID["DAILYMED-SPL-LISINOPRIL-002-CHUNK-01"])  # genuine-looking fetal toxicity text
    state = frozen_state([], verifier)
    state.retrieval_engine = StubRetrieval([as_candidate(fetal)])
    state.verified_source_links = {fetal["chunk_id"]: fetal["document_url"]}  # even if its identity held
    kind, data, _, _ = run(state)
    assert kind == "abstention"
    assert data["claims"][0]["support_state"] != "SUPPORTED"
    assert data["evidence"][0]["claim_support_status"] == "NO_VERIFIED_CLAIM"


# ── Test N: duplicate records ────────────────────────────────────────────────

def test_duplicate_records_count_as_one_piece_of_evidence(approved_candidate, verifier):
    (item,) = approved_candidate.relationship_store.evidence
    twin = dict(item, chunk_id=item["chunk_id"] + "-DUP")
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(), retrieval_engine=StubRetrieval([as_candidate(item), as_candidate(twin)]),
        llm_backend=CountingLLM(), claim_verifier=verifier, model_init_errors={},
        relationship_store=approved_candidate.relationship_store,
        shared_source_urls=approved_candidate.shared_source_urls,
        verified_source_links={item["chunk_id"]: item["document_url"], twin["chunk_id"]: twin["document_url"]},
    )
    _, data, _, _ = run(state)
    assert [e["chunk_id"] for e in data["evidence"]] == [item["chunk_id"]]


# ── Test O: missing source service ───────────────────────────────────────────

def test_a_failed_evidence_source_is_a_system_error_without_citations(verifier):
    class Down:
        def retrieve(self, *a, **k):
            raise ConnectionError("source connector unavailable")
    state = frozen_state([], verifier)
    state.retrieval_engine = Down()
    kind, data, _, _ = run(state)
    assert kind == "error" and data["code"] == "RETRIEVAL_ERROR"
    assert "not an evidence finding" in data["message"] and "evidence" not in data


# ── Test F at the pipeline level: every provider fails ───────────────────────

def test_when_every_provider_fails_the_stream_ends_with_one_llm_error(approved_candidate, verifier):
    err = ModelExecutionError("All LLM providers failed", status_code="ALL_PROVIDERS_FAILED")
    err.failure_class = FailureClass.MODEL_NOT_FOUND
    err.attempts = [{"provider": "nvidia", "failure_class": "MODEL_NOT_FOUND", "decision": "failover"},
                    {"provider": "groq", "failure_class": "MODEL_NOT_FOUND", "decision": "stop"}]
    (item,) = approved_candidate.relationship_store.evidence
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(), retrieval_engine=StubRetrieval([as_candidate(item)]),
        llm_backend=CountingLLM(error=err), claim_verifier=verifier, model_init_errors={},
        relationship_store=approved_candidate.relationship_store,
        shared_source_urls=approved_candidate.shared_source_urls,
        verified_source_links=approved_candidate.verified_source_links,
    )
    kind, data, _, events = run(state)
    assert kind == "error" and data["code"] == "LLM_ERROR" and data["served_by"] is None
    assert data["failure_class"] == "MODEL_NOT_FOUND"
    assert [a["provider"] for a in data["provider_attempts"]] == ["nvidia", "groq"]
    assert not any(e["event"] in ("answer", "complete") for e in events)
    assert {"stage": "generating", "status": "failed"}.items() <= next(
        e["data"] for e in events if e["event"] == "stage_update" and e["data"].get("status") == "failed").items()
