"""Warfarin + ibuprofen through the real live pipeline: the frozen corpus's placeholder sources.

Tests built on candidate evidence that is still pending researcher approval are kept outside version
control until it is reviewed.
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
from adaptive_trust_medical_rag.services.live_source_links import shared_urls
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
RXCUI = {"warfarin": "11289", "ibuprofen": "5640"}
CLAIM = ("Warfarin interacts with ibuprofen and can increase the risk of bleeding; patients should be "
         "closely monitored [Source 1].")


def as_candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item.get("document_url", ""), source_authority=item.get("authority", 0.5),
        metadata={"provenance": item.get("provenance", {}), "source_type": item.get("source_type"),
                  "freshness_score": item.get("freshness", 0.8), "source_identity": item.get("source_identity"),
                  "supported_claims": item.get("supported_claims")},
    ))


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
