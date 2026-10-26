"""Every medication a released statement names must be a confirmed medication of the analysis and be named by a
source it cites (round 5, probe P01: "Enalapril ..." cited to the lisinopril label was released)."""

import pytest

from adaptive_trust_medical_rag.verification.canonical_identity import RequestDrugMap, medication_identity_violation

CONFIRMED = RequestDrugMap({"lisinopril": "29046", "spironolactone": "9997", "zestril": "29046"})
SEC_55 = "5.5 Hyperkalemia Serum potassium should be monitored periodically in patients receiving lisinopril."
SEC_71 = "7.1 Diuretics Potassium-sparing diuretics (spironolactone, amiloride, triamterene) can increase the risk."


@pytest.mark.parametrize(("statement", "cited", "expected"), [
    ("Enalapril can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication this analysis did not confirm: enalapril"),
    ("Lisinopril, like captopril, can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication this analysis did not confirm: captopril"),
    ("Spironolactone can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication its cited sources do not mention: spironolactone"),
    # A confirmed brand is not its generic's label: brands and generics are not assumed interchangeable.
    ("Zestril can cause hyperkalemia [Source 1].", [SEC_55],
     "names a medication its cited sources do not mention: zestril"),
])
def test_an_unconfirmed_or_uncited_medication_is_named(statement, cited, expected):
    assert medication_identity_violation(statement, CONFIRMED, cited) == expected


@pytest.mark.parametrize(("statement", "cited"), [
    ("Lisinopril can cause hyperkalemia [Source 1].", [SEC_55]),
    ("Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia [Source 2].", [SEC_71]),
    ("Lisinopril interacts with spironolactone [Source 1] [Source 2].", [SEC_55, SEC_71]),
    ("ACE inhibitors can cause hyperkalemia [Source 1].", [SEC_55]),  # a class, not a medication
    ("Serum potassium should be monitored periodically [Source 1].", [SEC_55]),  # names no medication
])
def test_confirmed_medications_named_by_a_cited_source_pass(statement, cited):
    assert medication_identity_violation(statement, CONFIRMED, cited) is None


def test_a_name_inside_another_word_does_not_count():
    assert medication_identity_violation("Lisinopril can cause hyperkalemia.", CONFIRMED, ["Lisinoprilate."]) == (
        "names a medication its cited sources do not mention: lisinopril")
