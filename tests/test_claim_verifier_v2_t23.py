import pytest
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2, EvidenceChunk, GateDecision, FinalSupportState, NLIInferenceError, NLIStatus
import os

cache_dir = os.path.abspath('cognee_service/model_cache/huggingface')

@pytest.fixture(scope="module")
def verifier():
    return ClaimVerifierV2(cache_dir=cache_dir)

def test_T23_nli_inference_error_preservation(verifier, monkeypatch):
    def mock_eval(premise, hypothesis):
        raise NLIInferenceError("Injected failure")
    monkeypatch.setattr(verifier, "_evaluate_pair", mock_eval)
    evidence = [EvidenceChunk("1", "chunk1")]
    # Use a long enough sentence so it becomes a valid claim
    report = verifier.verify("This is a valid test sentence.", evidence)
    assert report.judgments[0].support_state == FinalSupportState.INSUFFICIENT_EVIDENCE
    assert report.judgments[0].nli_status == NLIStatus.INFERENCE_ERROR
    assert "Injected failure" in report.judgments[0].nli_error
