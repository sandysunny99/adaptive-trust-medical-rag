"""Pin ClaimVerifierV2's conservative neutral rule (2026-10-26 audit, round 3, phase 2).

The state compares the best entailment with the highest neutral score of *any* evidence chunk. It
withholds some correct claims: "Lisinopril interacts with spironolactone, increasing risk of
hyperkalemia" was entailed by label section 7.1 at 0.998 and withheld because section 5.5 was neutral
at 0.999. A candidate fix that compared only the entailing chunk's own neutral score was tested with
the real NLI model (PubMedBERT-MNLI-MedNLI) and rejected: the model also gives section 7.1 an
entailment of 0.991 for "Lisinopril should be stopped immediately in all patients" and 0.568 for
"Lisinopril causes kidney failure in all patients", neither of which the label says, and both were
released as SUPPORTED. This rule is what withholds them, so it stays until a better or calibrated
NLI model is chosen (a research decision). The scores below are the real model's, scripted here so the
test is deterministic.
"""

from __future__ import annotations

import pytest

from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2, EvidenceChunk, FinalSupportState

S71, S55 = "label section 7.1", "label section 5.5"
REAL_SCORES = {
    "Lisinopril should be stopped immediately in all patients": {
        S71: {"entailment": 0.991, "neutral": 0.009, "contradiction": 0.0},
        S55: {"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0}},
    "Lisinopril causes kidney failure in all patients": {
        S71: {"entailment": 0.568, "neutral": 0.432, "contradiction": 0.001},
        S55: {"entailment": 0.002, "neutral": 0.998, "contradiction": 0.0}},
}


def judge(claim: str) -> FinalSupportState:
    v = ClaimVerifierV2()
    v._evaluate_pair = lambda premise, hypothesis: REAL_SCORES[claim][premise]
    evidence = [EvidenceChunk(chunk_id="7.1", text=S71, source_authority=0.95, citation_index=1),
                EvidenceChunk(chunk_id="5.5", text=S55, source_authority=0.95, citation_index=2)]
    (judgment,) = v.verify(claim + " [Source 1].", evidence).judgments
    return judgment.support_state


@pytest.mark.parametrize("claim", sorted(REAL_SCORES))
def test_a_false_entailment_below_another_chunks_neutral_score_is_not_supported(claim):
    assert judge(claim) != FinalSupportState.SUPPORTED
