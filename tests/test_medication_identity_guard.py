"""Every medication a released statement names must be named by a source it cites (round 5 probe P01: "Enalapril
..." cited to the lisinopril label; round 6 probe P06: "Furosemide ..." cited to its diuretics section)."""

import pytest

from adaptive_trust_medical_rag.normalization.medication_lexicon import MedicationLexicon, default_lexicon
from adaptive_trust_medical_rag.verification.canonical_identity import (
    RequestDrugMap,
    medication_findings,
    medication_identity_violation,
)

LEX = default_lexicon()  # the pinned RxNorm Current Prescribable Content lexicon (05-Oct-2026)
CONFIRMED = RequestDrugMap({"lisinopril": "29046", "spironolactone": "9997", "zestril": "29046"})
SEC_55 = ("5.5 Hyperkalemia Serum potassium should be monitored periodically in patients receiving lisinopril. Risk "
          "factors for the development of hyperkalemia include renal insufficiency, diabetes mellitus.")
SEC_71 = ("7.1 Diuretics Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood "
          "pressure. Potassium-sparing diuretics (spironolactone, amiloride, triamterene) can increase the risk.")


@pytest.mark.parametrize(("statement", "cited", "expected"), [
    ("Enalapril can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication this analysis did not confirm: Enalapril"),  # P01
    ("Furosemide can cause hyperkalemia in patients with renal insufficiency [Source 2].", [SEC_71],
     "names a medication this analysis did not confirm: Furosemide"),  # P06: recognised only by the lexicon
    ("Lisinopril, like captopril, can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication this analysis did not confirm: captopril"),
    ("Spironolactone can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication its cited sources do not mention: Spironolactone"),
    # A confirmed brand is not its generic's label: brands and generics are not assumed interchangeable.
    ("Zestril can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication its cited sources do not mention: Zestril"),
    # A drug-name suffix outside the lexicon is an unresolved identity, not a pass.
    ("Zorbipril can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication whose identity could not be resolved: zorbipril"),
])
def test_a_medication_the_cited_sources_do_not_name_is_withheld(statement, cited, expected):
    assert medication_identity_violation(statement, CONFIRMED, cited, LEX) == expected


@pytest.mark.parametrize(("statement", "cited"), [
    ("Lisinopril can cause hyperkalemia [Source 1].", [SEC_55]),
    ("Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia [Source 2].", [SEC_71]),
    ("Lisinopril interacts with spironolactone [Source 1] [Source 2].", [SEC_55, SEC_71]),
    ("ACE inhibitors can cause hyperkalemia [Source 1].", [SEC_55]),  # a class, not a medication
    ("Serum potassium should be monitored periodically [Source 1].", [SEC_55]),  # potassium: the source's context
    ("Amiloride can increase the risk of hyperkalemia [Source 2].", [SEC_71]),  # unconfirmed, named by its source
    ("Serum potassium‑sparing effects; renal insufficiency [Source 1].", [SEC_55]),
])
def test_medications_named_by_a_cited_source_pass(statement, cited):
    assert medication_identity_violation(statement, CONFIRMED, cited, LEX) is None


def test_findings_record_the_identity_and_the_grounding():
    (f,) = medication_findings("Furosemide can cause hyperkalemia [Source 2].", CONFIRMED, [SEC_71], LEX)
    assert f == {"text": "Furosemide", "rxcui": "4603", "rxnorm_name": "furosemide", "tty": "IN",
                 "status": "unconfirmed", "named_by_cited_source": False}


def test_salts_and_brands_are_distinct_identities():
    found = {f["text"]: (f["rxcui"], f["tty"]) for f in medication_findings(
        "Metoprolol succinate and metoprolol; Lasix and furosemide.", CONFIRMED, [], LEX)}
    assert found == {"Metoprolol succinate": ("221124", "PIN"), "metoprolol": ("6918", "IN"),
                     "Lasix": ("202991", "BN"), "furosemide": ("4603", "IN")}


def test_common_words_are_not_brand_names():
    # Brands match only as RxNorm writes them ("React", "Perform", "Align" are brands); lowercase prose is not.
    assert medication_findings("Patients may react; perform and align monitoring.", CONFIRMED, [], LEX) == []


def test_a_name_inside_another_word_does_not_count():
    assert medication_identity_violation("Lisinopril can cause hyperkalemia.", CONFIRMED, ["Lisinoprilate."], LEX) == (
        "names a medication its cited sources do not mention: Lisinopril")


def test_an_ambiguous_span_is_unresolved_unless_the_source_names_it():
    lex = MedicationLexicon([{"rxcui": "1", "name": "duoxa", "tty": "IN"}, {"rxcui": "2", "name": "Duoxa", "tty": "BN"}])
    assert medication_identity_violation("Duoxa can cause hyperkalemia.", CONFIRMED, [SEC_55], lex) == (
        "names a medication whose identity could not be resolved: Duoxa")
    assert medication_identity_violation("Duoxa can cause hyperkalemia.", CONFIRMED, ["Duoxa label."], lex) is None


def test_without_a_verified_lexicon_every_statement_fails():
    assert medication_identity_violation("Serum potassium should be monitored [Source 1].", CONFIRMED, [SEC_55], None) == (
        "medication lexicon unavailable, so medication identity cannot be checked")


def test_known_boundary_a_name_outside_the_lexicon_and_the_suffixes_is_not_seen():
    # Metamizole is not US-marketed (absent from the prescribable subset); an invented name has no drug suffix.
    assert medication_findings("Metamizole or Zorbitrex can cause hyperkalemia.", CONFIRMED, [], LEX) == []
