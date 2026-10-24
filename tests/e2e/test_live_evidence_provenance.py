"""Evidence provenance gates for the lisinopril + spironolactone regression.

Source identity is a hard gate separate from every score: a chunk is evidence only when its source
identity is verified, and only an approved V2 evidence record with a complete source identity
record makes it so. Placeholder DailyMed links, the PubMed ID shared by unrelated documents and
unverified links are excluded before generation, whatever their authority or trust score.

These tests use only the frozen corpus in data/. Tests built on candidate evidence that is still pending
researcher approval are kept outside version control until it is reviewed. The claim verifier is the real
ClaimVerifierV2.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services.live_application import (
    LiveMedicalRAGService,
)
from adaptive_trust_medical_rag.services.live_source_links import (
    check_source_identity,
    shared_urls,
    source_identity_status,
    source_link,
)
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
BY_ID = {item["chunk_id"]: item for item in CORPUS}
RXCUI = {"lisinopril": "29046", "spironolactone": "9997"}
CLAIM = "Lisinopril interacts with spironolactone and can increase the risk of hyperkalemia [Source 1]."


def as_candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item.get("document_url", ""), source_authority=item.get("authority", 0.5),
        metadata={"provenance": item.get("provenance", {}), "source_type": item.get("source_type"),
                  "freshness_score": item.get("freshness", 0.8), "source_identity": item.get("source_identity"),
                  "supported_claims": item.get("supported_claims")},
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
