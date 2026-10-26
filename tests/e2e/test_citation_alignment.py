"""Citation-to-evidence alignment through the real live pipeline (round 5, eval example E25).

Two real lisinopril label sections are retrieved: Source 1 is section 5.5 (hyperkalemia; FOOD-0001)
and Source 2 is section 7.1 (diuretics; REL-LIVE-0003). Both are approved only inside tmp_path.

The NLI is replaced by a classifier that entails every pair. That is the observed failure, not a
caricature: the pinned PubMedBERT-MNLI-MedNLI scored 0.998 entailment for "Lisinopril can cause
hyperkalemia in patients with renal insufficiency" against section 7.1, which never mentions renal
insufficiency (2026-10-26). So any withholding here comes from a deterministic gate, not the model.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import _lazy_init_models
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2

from test_live_evidence_provenance import CountingLLM, OfflineNormalizer, StubRetrieval, as_candidate, run

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
REL_DIR = ROOT / "data" / "live_medical" / "relationships"
NAMES = ("LIVE_RELATIONSHIP_RECORDS_V2.json", "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
         "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json")
SEC_55, SEC_71 = "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5", "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1"
E25 = "Lisinopril can cause hyperkalemia in patients with renal insufficiency"


class FixedNLI:
    """A classifier returning the same scores for every pair (shaped like the HF pipeline output)."""

    class _Config:
        id2label = {0: "entailment", 1: "neutral", 2: "contradiction"}

    def __init__(self, entailment, neutral, contradiction):
        self.model = SimpleNamespace(config=self._Config())
        self.scores = [{"label": "entailment", "score": entailment}, {"label": "neutral", "score": neutral},
                       {"label": "contradiction", "score": contradiction}]

    def __call__(self, inputs, **kwargs):
        return [self.scores]


def verifier_with(nli) -> ClaimVerifierV2:
    v = ClaimVerifierV2()  # TESTING=1: built around the keyword stand-in, then given the fixed classifier
    v.classifier = nli
    return v


OVER_ENTAILING = FixedNLI(0.998, 0.001, 0.001)
AMBIGUOUS = FixedNLI(0.45, 0.10, 0.45)
ENT, NEU = (0.998, 0.001, 0.001), (0.001, 0.998, 0.001)


class SectionNLI(FixedNLI):
    """Scripted scores per label section (found by its heading in the premise), so the cited and an
    uncited section can get different verdicts on the real verifier and gate path."""

    HEADINGS = {"s5_5": "5.5 Hyperkalemia", "s7_1": "7.1 Diuretics"}

    def __init__(self, **by_section):
        super().__init__(*ENT)
        self.by_heading = {self.HEADINGS[k]: v for k, v in by_section.items()}

    def __call__(self, inputs, **kwargs):
        matches = [v for k, v in self.by_heading.items() if k in inputs["text"]]
        assert len(matches) == 1, f"no single section heading in premise: {inputs['text'][:80]!r}"
        (e, n, c), = matches
        return [[{"label": "entailment", "score": e}, {"label": "neutral", "score": n},
                 {"label": "contradiction", "score": c}]]


def put(root: Path, folder: str, fixture: str, severity="MODERATE"):
    """A candidate copied into root/v2/<folder> and approved there only, with a test-only severity."""
    dest = root / "v2" / folder
    dest.mkdir(parents=True)
    src = FIX / fixture
    records = json.loads((src / NAMES[0]).read_text(encoding="utf-8"))
    for r in records["records"]:
        r["severity"] = severity  # test-only grade, not a clinical one
    rec_raw = (json.dumps(records) + "\n").encode()
    ev_raw = (src / NAMES[1]).read_bytes().replace(b"\r\n", b"\n")
    (dest / NAMES[0]).write_bytes(rec_raw)
    (dest / NAMES[1]).write_bytes(ev_raw)
    manifest = json.loads((src / NAMES[2]).read_text(encoding="utf-8"))
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL"
    manifest.update(status="APPROVED", approval={"approved_by": "Test fixture", "approved_at": "2026-10-26"},
                    records_sha256=hashlib.sha256(rec_raw).hexdigest(), evidence_sha256=hashlib.sha256(ev_raw).hexdigest())
    (dest / NAMES[2]).write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def loaded(tmp_path, monkeypatch):
    put(tmp_path, "a_food_0001", "food_0001_candidate")
    put(tmp_path, "b_rel_live_0003", "rel_live_0003_candidate")
    for name in ("LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json", "LIVE_RELATIONSHIP_RECORDS_V1.json"):
        shutil.copyfile(REL_DIR / name, tmp_path / name)
    monkeypatch.setattr(live_relationships, "RELATIONSHIP_DIR", str(tmp_path))
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    _lazy_init_models(state)
    by_id = {e["chunk_id"]: e for e in state.relationship_store.evidence}
    assert set(by_id) == {SEC_55, SEC_71} and set(state.verified_source_links) == {SEC_55, SEC_71}
    state.by_id = by_id
    return state


def analyse(loaded, conclusion, *, drugs=("Lisinopril",), nli=OVER_ENTAILING):
    """Run the live pipeline with Source 1 = section 5.5 and Source 2 = section 7.1."""
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval([as_candidate(loaded.by_id[SEC_55]), as_candidate(loaded.by_id[SEC_71])]),
        llm_backend=CountingLLM({"conclusion": conclusion}), claim_verifier=verifier_with(nli), model_init_errors={},
        relationship_store=loaded.relationship_store, shared_source_urls=loaded.shared_source_urls,
        verified_source_links=loaded.verified_source_links)
    kind, data, _, events = run(state, drugs=drugs)
    evidence = next(e["data"] for e in events if e["event"] in ("answer", "abstention"))
    return kind, data, evidence


def sources(data):
    return [ev["chunk_id"] for ev in data.get("evidence", [])]


# Review case 2 (E25): the same true claim, cited to its supporting section and to the wrong one.
def test_a_supported_claim_cited_to_its_section_is_released(loaded):
    kind, data, _ = analyse(loaded, f"{E25} [Source 1].")
    assert kind == "answer", data.get("claims")
    assert sources(data) == [SEC_55, SEC_71]  # Source N maps to the N-th eligible chunk


def test_the_same_claim_cited_to_the_wrong_section_is_withheld(loaded):
    kind, data, _ = analyse(loaded, f"{E25} [Source 2].")
    assert kind == "abstention"
    (claim,) = data["claims"]
    assert claim["support_state"] != "SUPPORTED"
    assert "renal" in claim["citation_alignment"] and "insufficiency" in claim["citation_alignment"]


# Review cases 1 and 6: a correctly cited paraphrase is not withheld for its wording. "kidney impairment" is
# in no retrieved section and "blood" only in 7.1, so no other section accounts for what 5.5 lacks.
def test_a_correctly_cited_paraphrase_is_not_withheld_for_its_wording(loaded):
    kind, data, _ = analyse(loaded, "Lisinopril can raise blood potassium in people with kidney impairment [Source 1].")
    assert kind == "answer", data.get("claims")
    assert "citation_alignment" not in data["claims"][0]


# Review case 3: both the cited and another section mention the content; the citation is not wrong.
def test_content_in_both_the_cited_and_another_section_is_not_misattributed(loaded):
    kind, data, _ = analyse(loaded, "Lisinopril can cause hyperkalemia [Source 2].")
    assert kind == "answer", data.get("claims")
    assert "citation_alignment" not in data["claims"][0]


# Review case 4: content found in no retrieved section is not called a wrong-section citation; the
# verifier decides (the scripted classifier entails everything, so only the absence of the label is asserted).
def test_content_in_no_retrieved_section_is_left_to_the_verifier(loaded):
    _, data, _ = analyse(loaded, "Lisinopril can cause angioedema in black patients [Source 1].")
    assert "citation_alignment" not in data["claims"][0]


# Review case 5: the application's own field labels ("severity serious", "specific food/drink interaction")
# are not read as misattributed content, nor (round 5) a schema severity grade as an outcome-severity claim.
@pytest.mark.parametrize("grade", ["major", "serious"])
def test_structured_field_labels_are_not_misattributed(loaded, grade):
    state = SimpleNamespace(
        drug_normalizer=OfflineNormalizer(),
        retrieval_engine=StubRetrieval([as_candidate(loaded.by_id[SEC_55]), as_candidate(loaded.by_id[SEC_71])]),
        llm_backend=CountingLLM({
            "conclusion": "Lisinopril can cause hyperkalemia [Source 1].",
            "adverse_reactions": [{"drug": "Lisinopril", "reaction": "hyperkalemia", "severity": grade,
                                   "evidence_level": "SUPPORTED", "frequency": "", "source": "[Source 1]"}],
            "food_guidance": [{"drug": "Lisinopril", "administration": "", "food_relationship": "SPECIFIC FOOD/DRINK INTERACTION",
                               "timing": "", "food_interactions": [
                                   "Potassium-containing salt substitutes are a risk factor for hyperkalemia [Source 1]."],
                               "evidence_status": "VERIFIED", "source": "[Source 1]"}]}),
        claim_verifier=verifier_with(OVER_ENTAILING), model_init_errors={},
        relationship_store=loaded.relationship_store, shared_source_urls=loaded.shared_source_urls,
        verified_source_links=loaded.verified_source_links)
    kind, data, _, _ = run(state, drugs=("Lisinopril",))
    assert "claims" in data, (kind, {k: v for k, v in data.items() if k in ("code", "message", "reason")})
    fields = {c["field"]: c for c in data["claims"]}
    assert {"adverse_reactions", "food_guidance"} <= set(fields)
    assert all("citation_alignment" not in c for c in data["claims"]), data["claims"]
    assert all("SEVERITY" not in (c.get("strength_check") or "") for c in data["claims"]), data["claims"]


# Review case 8: no valid citation fails closed.
@pytest.mark.parametrize("cite", ["", " (Source 1)", " [Source]", " [Source 9]"],
                         ids=["no citation", "unbracketed", "incomplete marker", "never retrieved"])
def test_a_claim_without_a_valid_citation_is_withheld(loaded, cite):
    kind, data, _ = analyse(loaded, f"{E25}{cite}.")
    assert kind == "abstention" and data["claims"][0]["support_state"] != "SUPPORTED"


# Review case 7: several citations are judged together, on the cited sections only.
def test_a_relevant_and_an_irrelevant_citation_together_still_cover_the_claim(loaded):
    kind, data, _ = analyse(loaded, f"{E25} [Source 1] [Source 2].")
    assert kind == "answer", data.get("claims")


def test_a_claim_needing_two_sections_passes_only_when_both_are_cited(loaded):
    both = ("Lisinopril can cause hyperkalemia in patients with renal insufficiency, and its initiation in "
            "patients on diuretics may result in excessive reduction of blood pressure")
    kind, data, _ = analyse(loaded, f"{both} [Source 1] [Source 2].")
    assert kind == "answer", data.get("claims")
    kind, data, _ = analyse(loaded, f"{both} [Source 1].")
    assert kind == "abstention" and "blood" in data["claims"][0]["citation_alignment"]


# Review case 9: a class-level statement attributed to a specific pair stays withheld (by the pair identity check).
def test_a_class_level_warning_attributed_to_a_specific_pair_is_withheld(loaded):
    claim = "Initiating lisinopril in patients taking spironolactone may cause excessive reduction of blood pressure"
    kind, data, _ = analyse(loaded, f"{claim} [Source 2].", drugs=("Lisinopril", "Spironolactone"))
    assert kind == "abstention" and data["claims"][0]["support_state"] != "SUPPORTED"


# Review case 2: a section with related terminology but not the claimed relationship.
def test_related_terminology_is_not_the_claimed_relationship(loaded):
    kind, data, _ = analyse(loaded, "Lisinopril can cause hyperkalemia in patients with diabetes mellitus [Source 2].")
    assert kind == "abstention" and "diabetes" in data["claims"][0]["citation_alignment"]


# Review case 9: overstatement still withheld, by the existing strength check.
def test_an_overstatement_cited_to_its_section_is_still_withheld(loaded):
    kind, data, _ = analyse(loaded, "Lisinopril must always be stopped in patients with hyperkalemia [Source 1].")
    assert kind == "abstention" and data["claims"][0]["support_state"] != "SUPPORTED"


# Review case 10: a correct, correctly cited claim the NLI finds ambiguous stays withheld, and not by alignment.
def test_an_ambiguous_nli_result_stays_withheld_and_alignment_is_not_the_reason(loaded):
    kind, data, _ = analyse(loaded, f"{E25} [Source 1].", nli=AMBIGUOUS)
    assert kind == "abstention"
    (claim,) = data["claims"]
    assert claim["support_state"] != "SUPPORTED" and "citation_alignment" not in claim


# Controlled cases on the real decision path: the scripted NLI gives each section its own verdict.
LONE_COMMON_WORD = "Lisinopril can cause hyperkalemia in renal insufficiency, raising blood potassium [Source 1]."
CONTROLLED = [
    # (review case, statement, NLI for 5.5, NLI for 7.1, released?, gate that withholds)
    ("1 both sections support", "Lisinopril can cause hyperkalemia [Source 2].", ENT, ENT, True, None),
    ("2 only the uncited section supports", f"{E25} [Source 2].", ENT, NEU, False, "verifier"),
    ("2 the cited section over-entails (E25)", f"{E25} [Source 2].", ENT, ENT, False, "alignment"),
    ("3 paraphrase supported by its cited section",
     "Lisinopril can raise blood potassium in people with kidney impairment [Source 1].", ENT, NEU, True, None),
    ("4 no retrieved section supports", "Lisinopril can cause angioedema in black patients [Source 1].", NEU, NEU,
     False, "verifier"),
    # Known limit (fails safe): the lone missing word "blood" is in 7.1, so attribution is not verified, though
    # 7.1 does not support the statement. A word screen cannot tell it from a one-word misattribution.
    ("5 a lone common word found elsewhere", LONE_COMMON_WORD, ENT, NEU, False, "alignment"),
]


@pytest.mark.parametrize(("statement", "s55", "s71", "released", "gate"), [c[1:] for c in CONTROLLED],
                         ids=[c[0] for c in CONTROLLED])
def test_controlled_attribution_cases(loaded, statement, s55, s71, released, gate):
    kind, data, _ = analyse(loaded, statement, nli=SectionNLI(s5_5=s55, s7_1=s71))
    (claim,) = data["claims"]
    assert (kind == "answer") is released, claim
    assert ("citation_alignment" in claim) is (gate == "alignment"), claim
    if gate == "alignment":
        assert claim["citation_alignment"].startswith("attribution not verified: ")
    # The cited-chunk gate is reported on its own; the max entailment may come from an uncited chunk, and
    # the record names it instead of passing it off as the claim's evidence.
    cited_scores = s55 if "[Source 1]" in statement else s71
    assert claim["citation_supports_claim"] is (cited_scores == ENT), claim
    if gate == "verifier":
        assert claim["support_state"] != "SUPPORTED"
    if statement == f"{E25} [Source 2]." and s71 == NEU:
        assert claim["entailment_chunk_id"] == SEC_55  # named as the max's source, yet not what releases
    # The evidence list marks a section as support only when a verified claim cites it, never an uncited one.
    marked = {ev["chunk_id"] for ev in data.get("evidence", []) if ev.get("claim_support_status") == "SUPPORTS_VERIFIED_CLAIM"}
    assert marked == ({SEC_55 if "[Source 1]" in statement else SEC_71} if released else set()), data.get("evidence")


# Review case 7: a changed medication, population, severity, timing or action is withheld by a deterministic
# gate even when the NLI entails everything (the observed over-entailment). P01 is the real-model probe:
# "Enalapril ..." cited to the lisinopril section was released with entailment 0.997 before round 5's guard.
CHANGED_FACTS = [
    ("medication not confirmed (P01)", "Enalapril can cause hyperkalemia in patients with renal insufficiency [Source 1].",
     ("Lisinopril",), "medication_identity", "enalapril"),
    ("confirmed medication its cited source does not name",
     "Spironolactone can cause hyperkalemia in patients with renal insufficiency [Source 1].",
     ("Lisinopril", "Spironolactone"), "medication_identity", "spironolactone"),
    ("population", "Lisinopril can cause hyperkalemia in pediatric patients with renal insufficiency [Source 1].",
     ("Lisinopril",), "strength_check", "PEDIATRIC"),
    ("severity", "Lisinopril causes fatal hyperkalemia in patients with renal insufficiency [Source 1].",
     ("Lisinopril",), "strength_check", "SEVERITY"),
    ("timing", "Lisinopril causes hyperkalemia within 24 hours in patients with renal insufficiency [Source 1].",
     ("Lisinopril",), "strength_check", "DURATION"),
    ("action", "Lisinopril must be discontinued in patients with renal insufficiency [Source 1].",
     ("Lisinopril",), "strength_check", "CERTAINTY"),
]


@pytest.mark.parametrize(("statement", "drugs", "gate", "named"), [c[1:] for c in CHANGED_FACTS],
                         ids=[c[0] for c in CHANGED_FACTS])
def test_a_changed_fact_is_withheld_by_a_deterministic_gate(loaded, statement, drugs, gate, named):
    kind, data, _ = analyse(loaded, statement, drugs=drugs)
    (claim,) = data["claims"]
    # The scripted NLI let it through (the verifier released it on its cited chunk), so the withholding below is
    # the downstream deterministic gate's, not an upstream NLI result.
    assert claim["verifier_decision"] == "release" and claim["citation_supports_claim"] is True, claim
    assert kind == "abstention" and claim["support_state"] == "UNSUPPORTED", claim
    assert named in claim[gate], claim


# The guard does not withhold what it should not: a drug class, and a confirmed medication its cited section names.
@pytest.mark.parametrize(("statement", "drugs"), [
    ("ACE inhibitors such as lisinopril can cause hyperkalemia [Source 1].", ("Lisinopril",)),
    ("Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia [Source 2].",
     ("Lisinopril", "Spironolactone")),
], ids=["drug class", "contextual medication named by its source"])
def test_a_supported_class_or_contextual_mention_is_not_withheld_by_the_medication_guard(loaded, statement, drugs):
    kind, data, _ = analyse(loaded, statement, drugs=drugs)
    (claim,) = data["claims"]
    assert kind == "answer" and "medication_identity" not in claim, claim


# BLOCKING residual, not fixed: a medication name the application cannot recognise (no RxNorm lookup per claim
# word, no offline drug lexicon beyond the request's names, a fixed list and seven suffixes) is not seen by the
# guard. With the real pinned model this exact claim was released (round-5 replay probe P06: cited section 7.1
# entailment 0.999). Remove the xfail only when the full path withholds it.
@pytest.mark.xfail(strict=True, reason="BLOCKING: unrecognised medication names are not detected (replay P06 released)")
def test_known_gap_an_unrecognised_medication_name_is_withheld(loaded):
    kind, _, _ = analyse(loaded, "Furosemide can cause hyperkalemia in patients with renal insufficiency [Source 2].")
    assert kind == "abstention"
