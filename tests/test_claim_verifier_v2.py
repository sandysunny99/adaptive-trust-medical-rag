import os

import pytest

from adaptive_trust_medical_rag.verification.claim_verifier_v2 import (
    ClaimVerifierV2,
    EvidenceChunk,
    FinalSupportState,
    GateDecision,
    NLIInferenceError,
    NLIStatus,
)

cache_dir = os.path.abspath('cognee_service/model_cache/huggingface')

@pytest.fixture(scope="module")
def verifier():
    return ClaimVerifierV2(cache_dir=cache_dir)

def test_T01_all_supported_release(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    report = verifier.verify("Atorvastatin may cause muscle pain.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.SUPPORTED
    assert report.decision == GateDecision.release

def test_T02_supported_partial_qualify(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    report = verifier.verify("Atorvastatin may cause muscle pain, and the sky is blue.", evidence)
    assert report.decision == GateDecision.qualify

def test_T03_supported_unsupported_critical_abstain(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    answer = "Atorvastatin may cause muscle pain, and it cures cancer completely."
    report = verifier.verify(answer, evidence, critical_claim_indices=[1])
    assert report.decision == GateDecision.abstain

def test_T04_supported_ambiguous_abstain(verifier):
    evidence = [
        EvidenceChunk("c1", "Statin interacts with aspirin.", citation_index=1),
        EvidenceChunk("c2", "Statin does not interact with aspirin.", citation_index=2)
    ]
    report = verifier.verify("Statin interacts with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.AMBIGUOUS
    assert report.decision == GateDecision.abstain

def test_T05_contradiction_anywhere_abstain(verifier):
    evidence = [EvidenceChunk("c1", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=1)]
    report = verifier.verify("Statin interacts with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.CONTRADICTED
    assert report.decision == GateDecision.abstain

def test_T06_insufficient_critical_abstain(verifier):
    evidence = [EvidenceChunk("c1", "The sun is hot.", citation_index=1)]
    report = verifier.verify("Aspirin cures cancer.", evidence, critical_claim_indices=[0])
    assert report.decision == GateDecision.abstain

def test_T07_unrelated_bounded_negative_chunk_does_not_scope_block(verifier):
    evidence = [
        EvidenceChunk("c1", "Aspirin cures headaches.", citation_index=1),
        EvidenceChunk("c2", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=2)
    ]
    report = verifier.verify("Aspirin cures headaches.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.SUPPORTED

def test_T08_true_nli_pair_path_only(verifier):
    evidence = [EvidenceChunk("c1", "Aspirin cures headaches.", citation_index=1)]
    report = verifier.verify("Aspirin cures headaches.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.SUPPORTED

def test_T09_nli_pair_failure_fail_closed(verifier):
    evidence = [EvidenceChunk("c1", "Aspirin cures headaches.", citation_index=1)]
    try:
        verifier._evaluate_pair({"invalid": 123}, "test")
        assert False
    except NLIInferenceError:
        assert True

def test_T10_actual_model_id2label_normalization(verifier):
    assert "entailment" in verifier.label_map.values()
    assert "contradiction" in verifier.label_map.values()
    assert "neutral" in verifier.label_map.values()

def test_T11_parent_mixed_sentence_preserves_child_states(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    report = verifier.verify("Atorvastatin may cause muscle pain, and aspirin cures cancer.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.SUPPORTED
    assert report.judgments[1].support_state == FinalSupportState.INSUFFICIENT_EVIDENCE

def test_T12_parent_state_becomes_partially_supported(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    report = verifier.verify("Atorvastatin may cause muscle pain, and aspirin cures cancer.", evidence)
    assert report.judgments[0].parent_sentence_state == FinalSupportState.PARTIALLY_SUPPORTED

def test_T13_grounding_ratio_distinct_from_confidence(verifier):
    evidence = [EvidenceChunk("c1", "Atorvastatin may cause muscle pain.", citation_index=1)]
    report = verifier.verify("Atorvastatin may cause muscle pain.", evidence)
    assert hasattr(report, "grounding_ratio")
    assert not hasattr(report, "confidence")

def test_T14_wrong_citation_resolves_but_does_not_support(verifier):
    evidence = [
        EvidenceChunk("c1", "Statin may cause liver damage.", citation_index=1),
        EvidenceChunk("c2", "Aspirin can cause stomach bleeding.", citation_index=2)
    ]
    report = verifier.verify("Aspirin can cause stomach bleeding [Source 1].", evidence)
    assert report.judgments[0].citation_validation.citation_resolves == True
    assert report.judgments[0].citation_validation.citation_supports_claim == False

def test_T15_conflicting_evidence_ambiguous(verifier):
    evidence = [
        EvidenceChunk("c1", "Statin interacts with aspirin.", citation_index=1),
        EvidenceChunk("c2", "Statin does not interact with aspirin.", citation_index=2)
    ]
    report = verifier.verify("Statin interacts with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.AMBIGUOUS

def test_T16_bounded_negative_supported(verifier):
    evidence = [EvidenceChunk("c1", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=1)]
    report = verifier.verify("No clinically significant pharmacokinetic interaction was observed.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.SUPPORTED

def test_T17_overgeneralized_absolute_safety(verifier):
    evidence = [EvidenceChunk("c1", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=1)]
    report = verifier.verify("There is no interaction of any kind between statin and aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.UNSUPPORTED

def test_T18_statin_aspirin_positive_assertion(verifier):
    evidence = [EvidenceChunk("c1", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=1)]
    report = verifier.verify("Statin interacts with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.CONTRADICTED

def test_T19_no_interaction_universal_claim(verifier):
    evidence = [EvidenceChunk("c1", "No clinically significant pharmacokinetic drug-drug interactions have been observed.", citation_index=1)]
    report = verifier.verify("The combination is completely safe.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.UNSUPPORTED

def test_T20_multi_chunk_contradiction_case_A(verifier, monkeypatch):
    def mock_eval(premise, hypothesis):
        if premise == "chunk1": return {"entailment": 0.55, "contradiction": 0.10, "neutral": 0.35}
        if premise == "chunk2": return {"entailment": 0.20, "contradiction": 0.90, "neutral": 0.10}
        return {"entailment": 0, "contradiction": 0, "neutral": 1}
    monkeypatch.setattr(verifier, "_evaluate_pair", mock_eval)
    evidence = [EvidenceChunk("1", "chunk1"), EvidenceChunk("2", "chunk2")]
    report = verifier.verify("Statin does not interact with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.CONTRADICTED

def test_T21_multi_chunk_contradiction_case_A_reversed(verifier, monkeypatch):
    def mock_eval(premise, hypothesis):
        if premise == "chunk1": return {"entailment": 0.55, "contradiction": 0.10, "neutral": 0.35}
        if premise == "chunk2": return {"entailment": 0.20, "contradiction": 0.90, "neutral": 0.10}
        return {"entailment": 0, "contradiction": 0, "neutral": 1}
    monkeypatch.setattr(verifier, "_evaluate_pair", mock_eval)
    evidence = [EvidenceChunk("2", "chunk2"), EvidenceChunk("1", "chunk1")]
    report = verifier.verify("Statin does not interact with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.CONTRADICTED

def test_T22_multi_chunk_contradiction_case_B(verifier, monkeypatch):
    def mock_eval(premise, hypothesis):
        if premise == "chunk1": return {"entailment": 0.90, "contradiction": 0.02, "neutral": 0.08}
        if premise == "chunk2": return {"entailment": 0.10, "contradiction": 0.85, "neutral": 0.05}
        return {"entailment": 0, "contradiction": 0, "neutral": 1}
    monkeypatch.setattr(verifier, "_evaluate_pair", mock_eval)
    evidence = [EvidenceChunk("1", "chunk1"), EvidenceChunk("2", "chunk2")]
    report = verifier.verify("Statin does not interact with aspirin.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.AMBIGUOUS

def test_T23_nli_inference_error_preservation(verifier, monkeypatch):
    def mock_eval(premise, hypothesis):
        raise NLIInferenceError("Injected failure")
    monkeypatch.setattr(verifier, "_evaluate_pair", mock_eval)
    evidence = [EvidenceChunk("1", "chunk1")]
    report = verifier.verify("This is a valid test sentence.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.INSUFFICIENT_EVIDENCE
    assert report.judgments[0].nli_status == NLIStatus.INFERENCE_ERROR
    assert "Injected failure" in report.judgments[0].nli_error

