"""An evidence URL is offered as a link only when it is verified for that chunk.

The frozen live corpus URLs were never checked against the documents they name, so every one
of them must be shown as text with the reason, never as a link to a possibly wrong page.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.services.live_source_links import (
    MISSING,
    PLACEHOLDER,
    SHARED,
    UNVERIFIED,
    VERIFIED,
    normalise_url,
    shared_urls,
    source_link,
)

CORPUS = Path(__file__).resolve().parents[2] / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json"


def corpus_statuses() -> dict[str, str]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    shared = shared_urls(data)
    return {item["chunk_id"]: source_link(item["chunk_id"], item.get("document_url"), shared=shared)["status"]
            for item in data}


def test_no_frozen_corpus_url_is_offered_as_a_link():
    statuses = corpus_statuses()
    assert len(statuses) == 14
    assert VERIFIED not in statuses.values()
    assert Counter(statuses.values()) == {PLACEHOLDER: 11, SHARED: 2, UNVERIFIED: 1}


def test_the_pubmed_id_given_to_two_unrelated_documents_is_shared():
    statuses = corpus_statuses()
    assert statuses["PUBMED-PMID-31234567-CHUNK-01"] == SHARED
    assert statuses["PUBMED-PUBMED-31234567-001-CHUNK-01"] == SHARED
    assert statuses["DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01"] == PLACEHOLDER
    assert statuses["OPENFDA-FDA-AE-9991-CHUNK-01"] == UNVERIFIED


def test_a_url_verified_for_the_chunk_is_a_link():
    url = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9aaffb41-408c-4372-8fd5-1d649450c0e9"
    assert source_link("c1", url, verified_links={"c1": url}) == {
        "status": VERIFIED, "note": "Verified link to the original document."}


@pytest.mark.parametrize(("verified", "url"), [
    ({"other": "https://dailymed.nlm.nih.gov/x"}, "https://dailymed.nlm.nih.gov/x"),   # verified for another chunk
    ({"c1": "https://dailymed.nlm.nih.gov/x"}, "https://dailymed.nlm.nih.gov/y"),      # a different URL
    ({"c1": "http://dailymed.nlm.nih.gov/x"}, "http://dailymed.nlm.nih.gov/x"),        # not https
])
def test_a_url_not_verified_for_this_chunk_is_not_a_link(verified, url):
    assert source_link("c1", url, verified_links=verified)["status"] == UNVERIFIED


@pytest.mark.parametrize("url", [
    "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-simvastatin",
    "https://example.org/c1",
    "https://www.example.com/paper",
])
def test_placeholder_urls_are_named_as_placeholders(url):
    assert source_link("c1", url)["status"] == PLACEHOLDER


def test_missing_url():
    assert source_link("c1", None)["status"] == source_link("c1", "")["status"] == MISSING


def test_trailing_slash_and_host_case_do_not_hide_a_shared_url():
    items = [{"document_id": "a", "document_url": "https://PubMed.ncbi.nlm.nih.gov/1/"},
             {"document_id": "b", "document_url": "https://pubmed.ncbi.nlm.nih.gov/1"},
             {"document_id": "c", "document_url": "https://pubmed.ncbi.nlm.nih.gov/2"}]
    assert shared_urls(items) == {normalise_url("https://pubmed.ncbi.nlm.nih.gov/1")}
