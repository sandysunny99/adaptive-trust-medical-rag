"""Live pipeline failure semantics: a system failure is never reported as an evidence finding,
and the answer gate releases only when every generated statement is verified.

Runs LiveMedicalRAGService.execute with stub normalizer, retrieval and LLM; no provider,
model download or network is contacted.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.services import live_application
from adaptive_trust_medical_rag.services.live_application import (
    LiveMedicalRAGService,
    _lazy_init_models,
    _LiveEmbeddingModel,
    _short_error,
    patient_context_text,
)
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import (
    AtomicClaim,
    CitationValidation,
    ClaimVerifierV2,
    FinalSupportState,
    GateDecision,
    SemanticJudgment,
    VerificationReportV2,
)

RXCUI = {"simvastatin": "36567", "clarithromycin": "21212"}
EVIDENCE = "Simvastatin is contraindicated with clarithromycin because it raises the risk of myopathy."
UNVERIFIED_MARK = "rhabdomyolysis-unverified"


# ── Harness ──────────────────────────────────────────────────────────────────

def chunk(text: str = EVIDENCE, *, authority: float = 0.9, content_hash: str | None = None) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id="c1",
        document_id="doc-c1",
        text=text,
        source_url="https://example.org/c1",
        source_authority=authority,
        metadata={
            "provenance": {
                "source": "DAILYMED", "document_id": "doc-c1", "chunk_id": "c1",
                "content_hash": content_hash or hashlib.sha256(text.encode("utf-8")).hexdigest(),
            },
            "source_type": "DAILYMED", "freshness_score": 0.9,
        },
    ))


class StubRetrieval:
    def __init__(self, chunks=None, error: Exception | None = None):
        self.chunks = [chunk()] if chunks is None else chunks
        self.error = error

    def retrieve(self, query, query_drugs, top_k=20):
        if self.error:
            raise self.error
        return self.chunks


class OfflineNormalizer:
    async def normalize_batch(self, names):
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI[n.lower()], brand_name=None,
                                formulation=None, confidence=1.0, source="TEST") for n in names]


class StubLLM:
    def __init__(self, answer: dict):
        self.content = json.dumps(answer)

    async def generate_structured(self, prompt, response_format, provider_name=None):
        return SimpleNamespace(content=self.content, provider="mock", model="mock-llm")


class FailingLLM:
    async def generate_structured(self, prompt, response_format, provider_name=None):
        raise RuntimeError("cloudflare timeout")


class ServingLLM:
    """A provider response as the OpenAI-compatible adapter builds it, with the provider's own model field."""

    def __init__(self, answer: dict):
        self.content = json.dumps(answer)
        self.provider_names: list[str | None] = []

    async def generate_structured(self, prompt, response_format, provider_name=None):
        self.provider_names.append(provider_name)
        return SimpleNamespace(content=self.content, provider="cloudflare",
                               model="@cf/meta/llama-3.3-70b-instruct-fp8-fast", finish_reason="stop",
                               raw_metadata={"model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                                             "choices": [{"message": {"content": self.content}}]})


def report(text: str, *states: FinalSupportState) -> VerificationReportV2:
    claim = AtomicClaim(text=text, parent_sentence=text, claim_index=0)
    judgments = [
        SemanticJudgment(
            claim=claim, entailment=0.9, contradiction=0.0, neutral=0.1,
            best_entailment_chunk_id="c1", best_contradiction_chunk_id=None, best_neutral_chunk_id=None,
            support_state=state, citation_validation=CitationValidation(True, True, True, False),
            parent_sentence_state=state,
        )
        for state in states
    ]
    decision = GateDecision.release if set(states) == {FinalSupportState.SUPPORTED} else GateDecision.qualify
    return VerificationReportV2([claim], judgments, 1.0, decision, "scripted")


class RawLLM:
    """Returns text exactly as a provider sent it, with the provider's stop reason."""

    def __init__(self, content: str, finish_reason: str):
        self.content, self.finish_reason = content, finish_reason

    async def generate_structured(self, prompt, response_format, provider_name=None):
        return SimpleNamespace(content=self.content, provider="cloudflare", model="cf-model",
                               finish_reason=self.finish_reason)


class ScriptedVerifier:
    """SUPPORTED for every statement except those containing UNVERIFIED_MARK."""

    def __init__(self):
        self.texts: list[str] = []

    def verify(self, answer, evidence, **kwargs):
        self.texts.append(answer)
        if UNVERIFIED_MARK in answer:
            return report(answer, FinalSupportState.UNSUPPORTED)
        return report(answer, FinalSupportState.SUPPORTED)


class QualifyVerifier:
    """Partial support: one judgment supported, one not (the V2 'qualify' decision)."""

    def verify(self, answer, evidence, **kwargs):
        return report(answer, FinalSupportState.SUPPORTED, FinalSupportState.UNSUPPORTED)


class RaisingVerifier:
    def verify(self, answer, evidence, **kwargs):
        raise RuntimeError("NLI backend crashed")


class EmptyReportVerifier:
    """Claims it released, but judged nothing."""

    def verify(self, answer, evidence, **kwargs):
        return VerificationReportV2([], [], 1.0, GateDecision.release, "All claims supported.")


ANSWER = {
    "conclusion": "Simvastatin and clarithromycin should not be combined [Source 1].",
    "interactions": [{
        "drug_a": "Simvastatin", "drug_b": "Clarithromycin", "interaction_detected": True,
        "interaction_type": "contraindicated combination", "potential_effect": "myopathy",
        "severity": "major", "evidence_status": "VERIFIED INTERACTION", "sources": ["Source 1"],
        "note": "text outside the schema is never released",
    }],
    "adverse_reactions": [{"drug": "Simvastatin", "reaction": "myopathy", "severity": "major",
                           "evidence_level": "SUPPORTED", "source": "Source 1"}],
    "warnings": ["Do not take simvastatin with clarithromycin [Source 1]."],
    "food_guidance": [{"drug": "Simvastatin", "administration": "once daily in the evening",
                       "food_relationship": "WITH_OR_WITHOUT_FOOD", "evidence_status": "LIMITED",
                       "source": "Source 1"}],
    "patient_considerations": [{"factor": "age", "provided": True, "evidence_found": True,
                                "consideration": "myopathy risk rises with age",
                                "evidence_status": "LIMITED", "source": "Source 1"}],
    "claims_for_verification": ["Clarithromycin raises simvastatin exposure [Source 1]."],
}

NO_VERIFIER = object()


def run(answer: dict | None = None, *, retrieval=None, verifier=None, monkeypatch=None,
        init_errors: dict | None = None, retrieval_info: dict | None = None, llm=None,
        llm_selection: dict | None = None, **state_extra):
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval() if retrieval is None else retrieval,
        llm_backend=llm or StubLLM(ANSWER if answer is None else answer),
        claim_verifier=None if verifier is NO_VERIFIER else (verifier or ScriptedVerifier()),
        model_init_errors=init_errors or {},
        **state_extra,
    )
    if retrieval_info is not None:
        state.retrieval_info = retrieval_info
    if retrieval is False:
        state.retrieval_engine = None
    if monkeypatch is not None:
        # Keep the state as given: no lazy model load fills in what the test removed.
        monkeypatch.setattr(live_application, "_lazy_init_models", lambda app_state: None)

    async def collect():
        service = LiveMedicalRAGService(state)
        return [e async for e in service.execute("req-semantics", ["Simvastatin", "Clarithromycin"], None, 0,
                                                 llm_selection=llm_selection)]

    return asyncio.run(collect()), state


def outcome(events):
    terminal = [e for e in events if e["event"] in ("answer", "abstention", "error")]
    assert len(terminal) == 1, [e["event"] for e in events]
    return terminal[0]["event"], terminal[0]["data"]


def last_status(events, stage):
    statuses = [e["data"]["status"] for e in events
                if e["event"] == "stage_update" and e["data"].get("stage") == stage]
    return statuses[-1] if statuses else None


# ── Model initialisation records why retrieval is unavailable ───────────────

def test_missing_corpus_is_recorded_and_no_empty_engine_is_built(monkeypatch):
    monkeypatch.setattr(live_application, "LIVE_CORPUS_FILE", "NOT_A_CORPUS.json")
    state = SimpleNamespace(claim_verifier=object(), retrieval_engine=None)
    _lazy_init_models(state)
    assert state.retrieval_engine is None
    assert state.model_init_errors["retrieval"] == "live corpus file NOT_A_CORPUS.json not found"


def test_embedding_model_load_failure_is_recorded(monkeypatch):
    class Offline:
        def __init__(self, data):
            raise OSError("We couldn't connect to the model hub")

    monkeypatch.setattr(live_application, "_LiveEmbeddingModel", Offline)
    state = SimpleNamespace(claim_verifier=object(), retrieval_engine=None)
    _lazy_init_models(state)
    assert state.retrieval_engine is None
    assert state.model_init_errors["retrieval"] == (
        "embedding model all-MiniLM-L6-v2 could not be loaded "
        "(OSError: We couldn't connect to the model hub)"
    )


def test_query_embedding_dimension_must_match_the_corpus(monkeypatch):
    class WrongDimension:
        def __init__(self, name):
            self.name = name

        def encode(self, texts):
            return np.zeros((len(texts), 512))

    fake = ModuleType("sentence_transformers")
    fake.SentenceTransformer = WrongDimension
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake)
    monkeypatch.setenv("TESTING", "0")
    with pytest.raises(ValueError, match=r"dimension 512 does not match corpus dimension \[384\]"):
        _LiveEmbeddingModel([{"text": "a", "embedding": [0.0] * 384}])


def test_claim_verifier_failure_does_not_skip_retrieval(monkeypatch):
    def broken():
        raise RuntimeError("weights missing")

    monkeypatch.setattr(live_application, "ClaimVerifierV2", broken)
    state = SimpleNamespace(claim_verifier=None, retrieval_engine=None)
    _lazy_init_models(state)
    assert state.claim_verifier is None
    assert state.model_init_errors["claim_verifier"] == "RuntimeError: weights missing"
    assert state.retrieval_engine is not None
    assert "retrieval" not in state.model_init_errors
    # Under TESTING the query encoder is a stub; it is labelled so, never as real retrieval.
    assert state.retrieval_info == {
        "corpus": "LIVE_MEDICAL_CORPUS_V2", "chunk_count": 14,
        "embedding_model": "all-MiniLM-L6-v2", "embedding_mode": "testing_stub",
    }


# ── Retrieval outcomes are told apart ────────────────────────────────────────

def test_unavailable_retrieval_is_an_error_not_an_empty_search(monkeypatch):
    reason = "embedding model all-MiniLM-L6-v2 could not be loaded (OSError: offline)"
    events, _ = run(retrieval=False, monkeypatch=monkeypatch, init_errors={"retrieval": reason})
    kind, data = outcome(events)
    assert kind == "error"
    assert data["code"] == "RETRIEVAL_UNAVAILABLE"
    assert reason in data["message"]
    assert "not an evidence finding" in data["message"]
    assert last_status(events, "retrieving") == "failed"
    assert not any(e["event"] in ("retrieval", "trust") for e in events)


def test_retrieval_query_exception_is_an_error():
    events, _ = run(retrieval=StubRetrieval(error=RuntimeError("index corrupted")))
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "RETRIEVAL_ERROR")
    assert "RuntimeError" in data["message"]
    assert last_status(events, "retrieving") == "failed"


def test_search_with_no_results_abstains_and_says_the_search_ran():
    events, _ = run(retrieval=StubRetrieval(chunks=[]))
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "The search ran but found no evidence for these medications in the live corpus."
    assert last_status(events, "retrieving") == "complete"


def test_evidence_failing_provenance_abstains_with_that_reason():
    events, _ = run(retrieval=StubRetrieval(chunks=[chunk(content_hash="0" * 64)]))
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "1 evidence chunk(s) were retrieved, but all failed provenance or integrity checks."


def test_evidence_below_eligibility_abstains_with_that_reason():
    events, _ = run(retrieval=StubRetrieval(chunks=[chunk(authority=0.2)]))
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"].startswith(
        "1 evidence chunk(s) about these medications passed security checks, but none was eligible")
    assert "source authority of at least 0.30" in data["reason"]


def test_retrieval_event_labels_the_embedding_mode():
    info = {"corpus": "LIVE_MEDICAL_CORPUS_V2", "chunk_count": 14,
            "embedding_model": "all-MiniLM-L6-v2", "embedding_mode": "testing_stub"}
    events, _ = run(retrieval_info=info)
    (retrieval,) = [e["data"] for e in events if e["event"] == "retrieval"]
    assert retrieval["embedding_mode"] == "testing_stub"
    assert retrieval["embedding_model"] == "all-MiniLM-L6-v2"


# ── The answer gate fails closed ─────────────────────────────────────────────

def test_fully_verified_answer_is_released_and_every_field_was_verified():
    events, state = run()
    kind, data = outcome(events)
    assert kind == "answer"
    assert data["gate_decision"] == "release"
    verified = {c["field"] for c in data["claims"]}
    assert verified == {"conclusion", "interactions", "adverse_reactions", "warnings", "food_guidance",
                        "patient_considerations", "claims_for_verification"}
    assert len(state.claim_verifier.texts) == len(data["claims"]) == 7
    assert "note" not in data["interactions"][0]


def test_one_unverified_field_withholds_the_whole_answer():
    answer = json.loads(json.dumps(ANSWER))
    answer["adverse_reactions"][0]["reaction"] = UNVERIFIED_MARK
    events, _ = run(answer)
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "1 of 7 generated claims failed post-generation verification."
    (failed,) = [c for c in data["claims"] if c["support_state"] != "SUPPORTED"]
    assert failed["field"] == "adverse_reactions"


def test_missing_claim_verifier_abstains(monkeypatch):
    events, _ = run(verifier=NO_VERIFIER, monkeypatch=monkeypatch)
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "The claim verifier is not loaded, so the generated answer could not be verified."
    assert last_status(events, "claim_verifying") == "failed"


def test_answer_without_statements_abstains():
    events, _ = run({"conclusion": "", "interactions": [], "warnings": []})
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "The generated answer contained no statements that could be verified."


def test_verifier_exception_abstains_and_marks_the_stage_failed():
    events, _ = run(verifier=RaisingVerifier())
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["reason"] == "Claim verification failed with an error, so the answer was not verified."
    assert last_status(events, "claim_verifying") == "failed"
    assert all(c["verification_error"] == "RuntimeError" for c in data["claims"])


def test_partial_support_is_not_supported():
    events, _ = run(verifier=QualifyVerifier())
    kind, data = outcome(events)
    assert kind == "abstention"
    assert {c["support_state"] for c in data["claims"]} == {"UNSUPPORTED"}


def test_report_with_no_judgments_is_not_supported():
    events, _ = run(verifier=EmptyReportVerifier())
    kind, data = outcome(events)
    assert kind == "abstention"
    assert {c["support_state"] for c in data["claims"]} == {"INSUFFICIENT_EVIDENCE"}


def test_unknown_status_label_is_an_output_validation_failure():
    answer = json.loads(json.dumps(ANSWER))
    answer["interactions"][0]["evidence_status"] = "TOTALLY SAFE"
    events, _ = run(answer)
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "LLM_OUTPUT_VALIDATION_FAILURE")
    assert "interactions[0].evidence_status" in data["message"]
    assert last_status(events, "generating") == "failed"


def test_answer_cut_off_at_the_token_limit_says_so_and_logs_no_content(caplog):
    truncated = json.dumps(ANSWER)[:200]
    events, _ = run(llm=RawLLM(truncated, "length"))
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "LLM_OUTPUT_VALIDATION_FAILURE")
    assert data["message"].startswith("Failed to parse LLM structured output.")
    assert "output token limit" in data["message"]
    assert (data["finish_reason"], data["provider"], data["model_id"]) == ("length", "cloudflare", "cf-model")
    assert data["served_by"] == {"provider": "cloudflare", "model_id": "cf-model", "reported_model": None,
                                 "finish_reason": "length", "output_length": 200}
    assert last_status(events, "generating") == "failed"
    assert "finish_reason=length length=200" in caplog.text
    assert truncated[20:60] not in caplog.text


def test_answer_that_is_not_json_keeps_the_plain_parse_message():
    events, _ = run(llm=RawLLM("Here is the analysis you asked for.", "stop"))
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "LLM_OUTPUT_VALIDATION_FAILURE")
    assert data["message"] == "Failed to parse LLM structured output."
    assert data["finish_reason"] == "stop"


def test_source_that_is_not_a_retrieved_chunk_cannot_be_released():
    answer = json.loads(json.dumps(ANSWER))
    answer["interactions"][0]["sources"] = ["PMID 12345678"]
    events, _ = run(answer)
    kind, data = outcome(events)
    assert kind == "abstention"
    (failed,) = [c for c in data["claims"] if c["support_state"] != "SUPPORTED"]
    assert failed["invalid_source_references"] == ["PMID 12345678"]


def test_evidence_without_relationship_identity_is_named_in_the_reason():
    """The real verifier (TESTING keyword NLI) cannot match a claim to a relationship the
    evidence record does not carry, so the claims are unsupported and the reason says why."""
    events, _ = run({"conclusion": EVIDENCE}, verifier=ClaimVerifierV2())
    kind, data = outcome(events)
    assert kind == "abstention"
    (claim,) = data["claims"]
    assert claim["canonical_identity_status"] == "UNAVAILABLE"
    assert claim["support_state"] == "UNSUPPORTED"
    assert data["reason"] == (
        "1 of 1 generated claims failed post-generation verification. 1 of them could not be "
        "matched to a drug relationship because the evidence records carry no relationship identity."
    )


# ── What the user and the model are shown ───────────────────────────────────

def test_abstention_after_generation_carries_the_checked_evidence():
    events, _ = run(verifier=QualifyVerifier())
    kind, data = outcome(events)
    assert kind == "abstention"
    assert [e["chunk_id"] for e in data["evidence"]] == ["c1"]
    assert data["evidence_retrieved"] == 1
    assert data["trust"]["is_eligible"] is True


def test_evidence_with_an_unverified_url_is_not_offered_as_a_link():
    events, _ = run(verifier=QualifyVerifier())
    kind, data = outcome(events)
    (item,) = data["evidence"]
    assert item["source_name"] == "https://example.org/c1"
    assert item["source_link_status"] == "PLACEHOLDER"
    assert "does not identify the original document" in item["source_link_note"]
    assert "url" not in item


def test_evidence_with_a_verified_url_is_offered_as_a_link():
    events, _ = run(verifier=QualifyVerifier(), verified_source_links={"c1": "https://example.org/c1"})
    kind, data = outcome(events)
    (item,) = data["evidence"]
    assert (item["source_link_status"], item["url"]) == ("VERIFIED", "https://example.org/c1")


def test_abstention_before_generation_marks_the_evidence_ineligible():
    events, _ = run(retrieval=StubRetrieval(chunks=[chunk(authority=0.2)]))
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["trust"]["is_eligible"] is False
    assert data["evidence_retrieved"] == 1


def test_unspecified_patient_fields_are_left_out_not_sent_as_none():
    dumped = {"age": 58, "sex": "male", "known_allergies": [], "known_conditions": ["hyperlipidemia"],
              "current_medications": [], "pregnancy_status": None, "breastfeeding": False,
              "kidney_impairment": None, "liver_impairment": None}
    text = patient_context_text(dumped)
    assert text.startswith('{"age": 58, "sex": "male", "known_conditions": ["hyperlipidemia"], "breastfeeding": false}')
    assert "known_allergies" not in text and "current_medications" not in text
    assert "do not treat it as none, negative or normal" in text


def test_empty_patient_context_is_none_provided():
    assert patient_context_text(None) == "None provided."
    assert patient_context_text({"age": None, "known_allergies": []}) == "None provided."


def test_load_error_keeps_the_first_sentence():
    e = OSError("We couldn't connect to 'https://huggingface.co' to load the files. Check your internet connection.")
    assert _short_error(e) == "OSError: We couldn't connect to 'https://huggingface.co' to load the files."


# ── Every outcome names the provider and model that served it ───────────────

def test_released_answer_names_the_provider_and_model_that_served_it():
    events, _ = run()
    kind, data = outcome(events)
    assert kind == "answer"
    served = {"provider": "mock", "model_id": "mock-llm", "reported_model": None, "finish_reason": None,
              "output_length": len(json.dumps(ANSWER))}
    assert data["served_by"] == served
    (complete,) = [e["data"] for e in events if e["event"] == "complete"]
    assert complete["served_by"] == served


def test_abstention_after_generation_names_the_provider_and_model_that_served_it():
    events, _ = run(verifier=QualifyVerifier())
    kind, data = outcome(events)
    assert kind == "abstention"
    assert (data["served_by"]["provider"], data["served_by"]["model_id"]) == ("mock", "mock-llm")


def test_schema_failure_names_the_provider_and_model_that_served_it():
    answer = json.loads(json.dumps(ANSWER))
    answer["interactions"][0]["evidence_status"] = "TOTALLY SAFE"
    events, _ = run(answer)
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "LLM_OUTPUT_VALIDATION_FAILURE")
    assert (data["served_by"]["provider"], data["served_by"]["model_id"]) == ("mock", "mock-llm")


def test_served_by_is_read_from_the_provider_response_and_holds_no_content(caplog):
    caplog.set_level("INFO", logger=live_application.__name__)
    llm = ServingLLM(ANSWER)
    selection = {"mode": "manual", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"}
    events, _ = run(llm=llm, verifier=QualifyVerifier(), llm_selection=selection)
    kind, data = outcome(events)
    assert kind == "abstention"
    assert llm.provider_names == ["cloudflare"]
    assert data["served_by"] == {"provider": "cloudflare", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                                 "reported_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                                 "finish_reason": "stop", "output_length": len(llm.content)}
    assert "provider=cloudflare" in caplog.text
    assert ANSWER["conclusion"] not in caplog.text
    assert ANSWER["conclusion"] not in json.dumps(data["served_by"])


def test_rxnorm_event_names_how_each_drug_was_resolved():
    events, _ = run()
    (rxnorm,) = [e["data"] for e in events if e["event"] == "rxnorm"]
    assert [m["rxnorm_source"] for m in rxnorm["entities"]] == ["TEST", "TEST"]


def test_abstention_before_generation_says_no_model_served_it():
    events, _ = run(retrieval=StubRetrieval(chunks=[chunk(authority=0.2)]))
    kind, data = outcome(events)
    assert kind == "abstention"
    assert data["served_by"] is None


def test_provider_failure_names_only_the_requested_model():
    events, _ = run(llm=FailingLLM())
    kind, data = outcome(events)
    assert (kind, data["code"]) == ("error", "LLM_ERROR")
    assert data["served_by"] is None
    assert data["requested_model"] == {"mode": "auto", "provider": "auto", "model_id": "auto"}
