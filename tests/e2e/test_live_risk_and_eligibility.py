"""Live risk tier and evidence eligibility (Sandeep's decisions of 2026-10-14).

- A contraindicated or major interaction is R3 only on an approved, provenance-backed record;
  the names alone, an LLM severity label or an NLI score never raise or establish it.
- A chunk that names none of the requested medications is never eligible and never counts
  toward the trust score. A pairwise claim needs an approved record on the cited chunk.

Runs LiveMedicalRAGService.execute with the real live-corpus texts, a stub normalizer, stub
retrieval and a stub LLM; the claim verifier is ClaimVerifierV2 with its TESTING keyword NLI.
Relationship records here are synthetic test fixtures written to a temporary directory.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import TRUST_THRESHOLDS, LiveMedicalRAGService
from adaptive_trust_medical_rag.services.live_relationships import (
    RELATIONSHIP_DATASET,
    RelationshipStore,
    live_risk_tier,
    load_relationship_store,
    validate_record,
)
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
BY_ID = {item["chunk_id"]: item for item in CORPUS}

SIMVA_CHUNK = "DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01"
UNRELATED = ["DAILYMED-SPL-CARBAMAZEPINE-001-CHUNK-01", "OPENFDA-FDA-AE-9991-CHUNK-01",
             "DAILYMED-SPL-WARFARIN-001-CHUNK-01"]
RXCUI = {"simvastatin": "36567", "clarithromycin": "21212", "metformin": "6809", "atorvastatin": "83367"}
SPAN = BY_ID[SIMVA_CHUNK]["text"]  # names simvastatin (the label's drug) and clarithromycin
CLAIM = "Simvastatin with clarithromycin is contraindicated [Source 1]."


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record(**overrides) -> dict:
    base = {
        "record_id": "TEST-REL-1",
        "subject": {"name": "simvastatin", "rxcui": RXCUI["simvastatin"]},
        "object": {"name": "clarithromycin", "rxcui": RXCUI["clarithromycin"]},
        "predicate": "CONTRAINDICATION",
        "direction": "A_TO_B",
        "severity": "CONTRAINDICATED",
        "source_chunk_id": SIMVA_CHUNK,
        "source_content_hash": sha(BY_ID[SIMVA_CHUNK]["text"]),
        "evidence_span": SPAN,
    }
    base.update(overrides)
    return base


def write_dataset(tmp_path: Path, records: list[dict], *, status: str = "APPROVED",
                  approved_by: str | None = "Test reviewer", corrupt_hash: bool = False,
                  corpus: list[dict] | None = None) -> RelationshipStore:
    raw = json.dumps({"dataset_version": RELATIONSHIP_DATASET, "records": records}, indent=2).encode("utf-8")
    (tmp_path / f"{RELATIONSHIP_DATASET}.json").write_bytes(raw)
    manifest = {
        "dataset_version": RELATIONSHIP_DATASET,
        "records_file": f"{RELATIONSHIP_DATASET}.json",
        "records_sha256": "0" * 64 if corrupt_hash else hashlib.sha256(raw).hexdigest(),
        "status": status,
        "approval": {"approved_by": approved_by, "approved_at": "2026-10-14"} if approved_by else None,
    }
    (tmp_path / f"{RELATIONSHIP_DATASET}_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return load_relationship_store(CORPUS if corpus is None else corpus, directory=str(tmp_path))


def meds(*names: str) -> list[dict]:
    return [{"raw_text": n.title(), "canonical_name": n, "rxcui": RXCUI[n]} for n in names]


# ── Harness ──────────────────────────────────────────────────────────────────

def corpus_chunk(chunk_id: str, *, text: str | None = None, authority: float | None = None,
                 retrieval_score: float | None = None) -> ScoredCandidate:
    item = BY_ID.get(chunk_id, {})
    body = text if text is not None else item["text"]
    sc = ScoredCandidate(Candidate(
        chunk_id=chunk_id,
        document_id=item.get("document_id", f"doc-{chunk_id}"),
        text=body,
        source_url=item.get("document_url", f"https://example.org/{chunk_id}"),
        source_authority=float(item.get("authority", 0.95)) if authority is None else authority,
        metadata={
            "provenance": {"source": "DAILYMED", "chunk_id": chunk_id, "content_hash": sha(body)},
            "source_type": item.get("source_type", "DAILYMED"),
            "freshness_score": float(item.get("freshness", 0.9)),
            # Test-only reviewed wording: a pair claim is released only up to its source's reviewed action.
            "supported_claims": [{"text": body, "action": "AVOID"}],
        },
    ))
    if retrieval_score is not None:
        sc.score = retrieval_score
    return sc


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
    def __init__(self, answer: dict):
        self.content = json.dumps(answer)
        self.calls = 0

    async def generate_structured(self, prompt, response_format, provider_name=None):
        self.calls += 1
        return SimpleNamespace(content=self.content, provider="mock", model="mock-llm")


def run(chunks, *, store: RelationshipStore | None = None, answer: dict | None = None,
        drugs=("Simvastatin", "Clarithromycin"), identity_verified: bool = True):
    llm = CountingLLM(answer or {"conclusion": CLAIM})
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval(chunks),
        llm_backend=llm,
        claim_verifier=ClaimVerifierV2(),
        model_init_errors={},
        relationship_store=store,
        # Fixture assumption: these synthetic chunks stand in for identity-verified sources, so the
        # stages after the source-identity gate are what these tests exercise.
        verified_source_links=({sc.candidate.chunk_id: sc.candidate.source_url for sc in chunks}
                               if identity_verified else {}),
    )

    async def collect():
        service = LiveMedicalRAGService(state)
        return [e async for e in service.execute("req-risk", list(drugs), None, 0)]

    events = asyncio.run(collect())
    terminal = [e for e in events if e["event"] in ("answer", "abstention", "error")]
    assert len(terminal) == 1, [e["event"] for e in events]
    (trust,) = [e["data"] for e in events if e["event"] == "trust"] or [None]
    return terminal[0]["event"], terminal[0]["data"], trust, llm


# ── Risk tier ────────────────────────────────────────────────────────────────

def test_known_contraindicated_pair_with_an_approved_record_is_r3(tmp_path):
    store = write_dataset(tmp_path, [record()])
    tier, basis = live_risk_tier(meds("simvastatin", "clarithromycin"), store)
    assert tier == "R3"
    assert "TEST-REL-1" in basis and SIMVA_CHUNK in basis


def test_the_pair_names_alone_never_reach_r3():
    tier, basis = live_risk_tier(meds("simvastatin", "clarithromycin"), RelationshipStore())
    assert tier == "R2"
    assert "no approved severe relationship record" in basis


def test_an_unknown_pair_is_an_interaction_question():
    assert live_risk_tier(meds("metformin", "atorvastatin"), RelationshipStore())[0] == "R2"


def test_an_ordinary_single_drug_query_stays_low(tmp_path):
    store = write_dataset(tmp_path, [record()])
    assert live_risk_tier(meds("metformin"), store)[0] == "R0"
    # A record about the pair does not touch either drug analysed alone.
    assert live_risk_tier(meds("simvastatin"), store)[0] == "R0"


def test_a_moderate_record_does_not_raise_the_tier(tmp_path):
    store = write_dataset(tmp_path, [record(severity="MODERATE")])
    assert live_risk_tier(meds("simvastatin", "clarithromycin"), store)[0] == "R2"


def test_contradictory_records_keep_the_higher_tier(tmp_path):
    store = write_dataset(tmp_path, [record(), record(record_id="TEST-REL-2", severity="NONE", predicate="INTERACTION")])
    tier, basis = live_risk_tier(meds("simvastatin", "clarithromycin"), store)
    assert tier == "R3"
    assert "another approved record says no interaction" in basis


def test_r3_uses_the_configured_075_threshold(tmp_path):
    store = write_dataset(tmp_path, [record()])
    _, _, trust, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store)
    assert trust["risk_class"] == "R3"
    assert trust["threshold"] == 0.75
    config = yaml.safe_load((ROOT / "config" / "trust.yaml").read_text(encoding="utf-8"))
    assert TRUST_THRESHOLDS == {tier: float(v) for tier, v in config["thresholds"].items()}


def test_evidence_eligible_at_r2_is_not_eligible_once_r3_is_justified(tmp_path):
    weak = corpus_chunk(SIMVA_CHUNK, authority=0.45)
    kind, data, trust, llm = run([weak])
    assert trust["risk_class"] == "R2" and trust["is_eligible"] is True
    assert 0.60 <= trust["overall_score"] < 0.75

    store = write_dataset(tmp_path, [record()])
    kind, data, trust, llm = run([weak], store=store)
    assert kind == "abstention" and llm.calls == 0
    assert trust["risk_class"] == "R3" and trust["is_eligible"] is False
    assert "at least 0.75 for risk tier R3" in data["reason"]


def test_an_llm_severity_label_does_not_raise_the_tier():
    answer = {"conclusion": CLAIM, "interactions": [{
        "drug_a": "Simvastatin", "drug_b": "Clarithromycin", "interaction_detected": True,
        "interaction_type": "contraindicated", "potential_effect": "rhabdomyolysis", "severity": "contraindicated",
        "evidence_status": "VERIFIED INTERACTION", "sources": ["Source 1"]}]}
    kind, _, trust, _ = run([corpus_chunk(SIMVA_CHUNK)], answer=answer)
    assert trust["risk_class"] == "R2"
    assert kind == "abstention"


# ── Records: only approved, hash-matching, grounded ones load ───────────────

def test_a_candidate_dataset_loads_nothing(tmp_path):
    store = write_dataset(tmp_path, [record()], status="CANDIDATE_PENDING_RESEARCHER_APPROVAL", approved_by=None)
    assert store.records == ()
    assert live_risk_tier(meds("simvastatin", "clarithromycin"), store)[0] == "R2"


def test_approval_needs_a_named_person(tmp_path):
    assert write_dataset(tmp_path, [record()], approved_by=None).records == ()


def test_a_records_file_that_does_not_match_its_manifest_loads_nothing(tmp_path):
    store = write_dataset(tmp_path, [record()], corrupt_hash=True)
    assert store.status == "HASH_MISMATCH" and store.records == ()


def test_a_crlf_checkout_hashes_the_same(tmp_path):
    write_dataset(tmp_path, [record()])
    path = tmp_path / f"{RELATIONSHIP_DATASET}.json"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert len(load_relationship_store(CORPUS, directory=str(tmp_path)).records) == 1


@pytest.mark.parametrize("overrides, why", [
    ({"evidence_span": "Simvastatin is contraindicated with clarithromycin"}, "not verbatim"),
    ({"source_content_hash": "0" * 64}, "content hash does not match"),
    ({"source_chunk_id": "NOT-IN-CORPUS"}, "not in the live corpus"),
    ({"evidence_span": "Simvastatin is a cholesterol-lowering medication."}, "does not name both"),
    ({"predicate": "CAUSES_HARM"}, "bounded predicate set"),
    ({"severity": "SERIOUS"}, "severity"),
    ({"direction": "UNKNOWN"}, "direction is unknown"),
    ({"object": {"name": "clarithromycin", "rxcui": ""}}, "unresolved medication identity"),
])
def test_ungrounded_or_incomplete_records_are_rejected(tmp_path, overrides, why):
    rec, reason = validate_record(record(**overrides), BY_ID)
    assert rec is None and why in reason
    assert write_dataset(tmp_path, [record(**overrides)]).records == ()


def test_the_shipped_candidate_is_grounded_but_not_loaded():
    """The candidate in the repository validates against the corpus, but stays unused until approved."""
    directory = Path(live_relationships.RELATIONSHIP_DIR)
    manifest = json.loads((directory / f"{RELATIONSHIP_DATASET}_MANIFEST.json").read_text(encoding="utf-8"))
    raw = (directory / manifest["records_file"]).read_bytes()
    assert hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == manifest["records_sha256"]
    for rec in json.loads(raw)["records"]:
        assert validate_record(rec, BY_ID)[1] == "valid"
    store = load_relationship_store(CORPUS)
    assert manifest["status"] != "APPROVED"
    assert store.records == ()


# ── Eligibility: unrelated evidence is excluded ─────────────────────────────

def test_unrelated_high_authority_chunks_alone_cannot_pass_eligibility():
    chunks = [corpus_chunk(cid, retrieval_score=0.99) for cid in UNRELATED]
    kind, data, trust, llm = run(chunks)
    assert kind == "abstention" and llm.calls == 0
    assert trust["is_eligible"] is False
    assert trust["unrelated_excluded"] == 3
    # Nothing reached scoring, so there is no trust score (not a computed 0).
    assert trust["overall_score"] is None and trust["score_status"] == "NO_ELIGIBLE_EVIDENCE"
    assert data["reason"] == ("3 evidence chunk(s) passed security checks, but none names a requested "
                              "medication (simvastatin, clarithromycin), so none can support this analysis.")


def test_unrelated_chunks_neither_reach_the_model_nor_raise_the_trust_score():
    alone = run([corpus_chunk(SIMVA_CHUNK)])
    mixed = run([corpus_chunk(cid, retrieval_score=0.99) for cid in UNRELATED] + [corpus_chunk(SIMVA_CHUNK)])
    assert mixed[2]["overall_score"] == alone[2]["overall_score"]
    assert mixed[2]["unrelated_excluded"] == 3
    assert [e["chunk_id"] for e in mixed[1]["evidence"]] == [SIMVA_CHUNK]


def test_a_chunk_naming_one_requested_medication_stays_eligible():
    one = corpus_chunk("ATORVA-CLARI", text="Clarithromycin is a strong CYP3A4 inhibitor.")
    _, data, trust, _ = run([one])
    assert trust["is_eligible"] is True and trust["unrelated_excluded"] == 0


def test_a_similar_drug_name_is_not_a_match():
    near = corpus_chunk("ATORVA", text="Atorvastatin is contraindicated with strong CYP3A4 inhibitors.")
    kind, _, trust, llm = run([near])
    assert kind == "abstention" and llm.calls == 0 and trust["unrelated_excluded"] == 1


# ── Pairwise claims need an approved record on the cited chunk ──────────────

def test_a_supported_pairwise_record_lets_a_matching_claim_through(tmp_path):
    store = write_dataset(tmp_path, [record()])
    kind, data, trust, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store)
    assert trust["risk_class"] == "R3"
    assert kind == "answer", data
    (claim,) = data["claims"]
    assert claim["canonical_identity_status"] == "MATCH"
    assert claim["support_state"] == "SUPPORTED"


def test_missing_relationship_identity_abstains_even_at_high_entailment():
    """NLI alone never establishes a drug relationship."""
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)])
    assert kind == "abstention"
    (claim,) = data["claims"]
    assert claim["canonical_identity_status"] == "UNAVAILABLE"
    assert claim["support_state"] == "UNSUPPORTED"


def test_a_record_for_another_pair_gives_no_identity(tmp_path):
    # Grounded in the same chunk, but it links simvastatin to erythromycin, not clarithromycin.
    store = write_dataset(tmp_path, [record(object={"name": "erythromycin", "rxcui": "4053"},
                                            evidence_span=BY_ID[SIMVA_CHUNK]["text"])])
    assert len(store.records) == 1
    kind, data, trust, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store)
    assert trust["risk_class"] == "R2"
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "UNAVAILABLE"


def test_a_claim_about_a_different_pair_is_not_supported_by_the_record(tmp_path):
    store = write_dataset(tmp_path, [record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store,
                           answer={"conclusion": "Simvastatin with erythromycin is contraindicated [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["support_state"] == "UNSUPPORTED"


def test_a_claim_with_another_relation_does_not_match_the_record(tmp_path):
    store = write_dataset(tmp_path, [record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store,
                           answer={"conclusion": "Simvastatin inhibits clarithromycin [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "MISMATCH"
    assert "did not match an approved relationship record" in data["reason"]


def test_contradictory_records_give_no_identity_and_abstain(tmp_path):
    no_interaction = record(record_id="TEST-REL-2", severity="NONE", predicate="INTERACTION")
    store = write_dataset(tmp_path, [record(), no_interaction])
    kind, data, trust, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store)
    assert trust["risk_class"] == "R3"
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "UNAVAILABLE"


def test_contradicting_evidence_blocks_a_claim_the_record_matches(tmp_path):
    store = write_dataset(tmp_path, [record()])
    contrary = corpus_chunk("CONTRARY", text="Simvastatin does not interact with clarithromycin; no interaction was observed.")
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK), contrary], store=store,
                           answer={"conclusion": "Simvastatin with clarithromycin is a contraindicated interaction [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_status"] == "MATCH"
    assert data["claims"][0]["support_state"] != "SUPPORTED"


def test_a_record_is_not_attached_once_the_chunk_text_changes(tmp_path):
    store = write_dataset(tmp_path, [record()])
    altered = BY_ID[SIMVA_CHUNK]["text"] + " Updated."
    assert store.identity_for_chunk(SIMVA_CHUNK, altered, [RXCUI["simvastatin"], RXCUI["clarithromycin"]]) is None
    assert store.identity_for_chunk(SIMVA_CHUNK, BY_ID[SIMVA_CHUNK]["text"],
                                    [RXCUI["simvastatin"], RXCUI["clarithromycin"]]) is not None


def test_the_corpus_is_not_modified():
    manifest = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_MANIFEST_V2.json").read_text(encoding="utf-8"))
    assert manifest["corpus_version"] == "LIVE_MEDICAL_CORPUS_V2"
    for item in CORPUS:
        assert sha(item["text"]) == item["content_hash"]


# ── Claim wording: disclaimer, contraindication wording, drug order ─────────
# Sandeep's follow-up of 2026-10-14: handle these narrowly, keep exact identity matching.

from adaptive_trust_medical_rag.services.live_application import (  # noqa: E402
    answer_statements,
    remove_research_disclaimers,
)

DISCLAIMER = "This is a research output, not clinical advice."


def symmetric_record(**overrides) -> dict:
    return record(direction="BIDIRECTIONAL", **overrides)


def interaction_item(**overrides) -> dict:
    item = {"drug_a": "Simvastatin", "drug_b": "Clarithromycin", "interaction_detected": True,
            "interaction_type": "contraindicated combination",
            "potential_effect": "increased risk of myopathy and rhabdomyolysis",
            "severity": "Contraindicated", "evidence_status": "VERIFIED INTERACTION", "sources": ["Source 1"]}
    item.update(overrides)
    return item


@pytest.mark.parametrize("sentence", [
    DISCLAIMER,
    "This information is for research purposes only and is not a substitute for professional medical advice.",
    "Disclaimer: research output only; not for clinical use.",
])
def test_a_research_disclaimer_is_taken_out_of_the_conclusion(sentence):
    fields, statements = answer_statements({"conclusion": f"{CLAIM} {sentence}"})
    assert fields["conclusion"] == CLAIM
    assert fields["removed_disclaimers"] == [sentence]
    assert [s.text for s in statements] == [CLAIM]


@pytest.mark.parametrize("sentence", [
    "This research output is not clinical advice, but simvastatin is safe with clarithromycin.",
    "This is a research output: the combination is safe.",
    "Research output only [Source 1].",
    "Not medical advice: take 20 mg daily.",
    "Please consult your healthcare provider.",
])
def test_a_sentence_with_any_clinical_content_stays_and_is_verified(sentence):
    fields, statements = answer_statements({"conclusion": sentence})
    assert fields["removed_disclaimers"] == []
    assert [s.text for s in statements] == [sentence]


def test_a_conclusion_that_is_only_a_disclaimer_leaves_nothing_to_release():
    fields, statements = answer_statements({"conclusion": DISCLAIMER})
    assert fields["conclusion"] == "" and statements == []
    assert remove_research_disclaimers("") == ("", [])


def test_the_disclaimer_no_longer_blocks_a_verified_answer(tmp_path):
    store = write_dataset(tmp_path, [record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={"conclusion": f"{CLAIM} {DISCLAIMER}"})
    assert kind == "answer", data
    assert data["conclusion"] == CLAIM
    assert data["removed_disclaimers"] == [DISCLAIMER]
    assert [c["support_state"] for c in data["claims"]] == ["SUPPORTED"]


def test_without_an_approved_record_the_answer_still_abstains():
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], answer={
        "conclusion": f"{CLAIM} {DISCLAIMER}", "interactions": [interaction_item()]})
    assert kind == "abstention"
    assert data["removed_disclaimers"] == [DISCLAIMER]
    assert {c["canonical_identity_status"] for c in data["claims"]} == {"UNAVAILABLE"}


@pytest.mark.parametrize("labels, verb", [
    ({"severity": "Contraindicated"}, "is contraindicated with"),
    ({"severity": None, "interaction_type": "Contraindicated combination"}, "is contraindicated with"),
    ({"severity": "Major", "interaction_type": "CYP3A4 inhibition"}, "interacts with"),
    ({"severity": "Not contraindicated", "interaction_type": "CYP3A4 inhibition"}, "interacts with"),
    ({"interaction_detected": False}, "does not interact with"),
])
def test_an_interaction_item_states_the_relation_it_asserts(labels, verb):
    _, (statement,) = answer_statements({"interactions": [interaction_item(**labels)]})
    assert statement.text.startswith(f"Simvastatin {verb} Clarithromycin")


def test_a_contraindicated_item_matches_a_contraindication_record(tmp_path):
    store = write_dataset(tmp_path, [record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={"interactions": [interaction_item()]})
    assert kind == "answer", data
    assert data["claims"][0]["canonical_identity_status"] == "MATCH"


def test_interacts_with_is_not_treated_as_a_contraindication(tmp_path):
    store = write_dataset(tmp_path, [symmetric_record()])
    for answer in ({"interactions": [interaction_item(severity="Major", interaction_type="CYP3A4 inhibition")]},
                   {"conclusion": "Simvastatin interacts with clarithromycin [Source 1]."}):
        kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer=answer)
        assert kind == "abstention"
        assert data["claims"][0]["canonical_identity_status"] == "MISMATCH"
        assert "Predicate mismatch" in data["claims"][0]["canonical_identity_reason"]


REVERSED = "Clarithromycin with simvastatin is contraindicated [Source 1]."


def test_reversed_drug_order_matches_a_symmetric_record(tmp_path):
    store = write_dataset(tmp_path, [symmetric_record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={"conclusion": REVERSED})
    assert kind == "answer", data
    assert data["claims"][0]["canonical_identity_status"] == "MATCH"


def test_reversed_drug_order_does_not_match_a_directional_record(tmp_path):
    store = write_dataset(tmp_path, [record(direction="A_TO_B")])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={"conclusion": REVERSED})
    assert kind == "abstention"
    assert "Subject RxCUI mismatch" in data["claims"][0]["canonical_identity_reason"]


def test_a_symmetric_record_keeps_the_predicate_exact(tmp_path):
    """The fixture claim of the cloud run: reversed order and a different relation."""
    store = write_dataset(tmp_path, [symmetric_record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={
        "conclusion": "Clarithromycin with simvastatin increases the risk of myopathy and rhabdomyolysis [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["canonical_identity_reason"] == "Predicate mismatch: source=CONTRAINDICATION claim=INCREASES"


def test_a_symmetric_record_does_not_cover_another_pair(tmp_path):
    store = write_dataset(tmp_path, [symmetric_record()])
    kind, data, _, _ = run([corpus_chunk(SIMVA_CHUNK)], store=store, answer={
        "conclusion": "Erythromycin with simvastatin is contraindicated [Source 1]."})
    assert kind == "abstention"
    assert data["claims"][0]["support_state"] == "UNSUPPORTED"


def test_a_directional_predicate_cannot_be_recorded_as_bidirectional():
    rec, why = validate_record(record(predicate="INHIBITION", direction="BIDIRECTIONAL"), BY_ID)
    assert rec is None and "directional" in why
    rec, why = validate_record(symmetric_record(), BY_ID)
    assert rec is not None and rec.symmetric


def test_a_directional_record_is_never_reoriented():
    rec, _ = validate_record(record(predicate="INHIBITION", direction="A_TO_B"), BY_ID)
    reversed_order = (RXCUI["clarithromycin"], RXCUI["simvastatin"])
    identity = rec.identity(reversed_order)
    assert (identity.subject_rxcui, identity.direction.value) == (RXCUI["simvastatin"], "A_TO_B")
