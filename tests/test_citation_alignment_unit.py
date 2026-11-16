"""The citation-alignment screen on its own: a statement whose cited source lacks words that one other
retrieved source contains in full has an unverified attribution."""

import pytest

from adaptive_trust_medical_rag.services.citation_alignment import (
    citation_alignment_violation,
    content_terms,
    misattributed_terms,
    uncited_terms,
)

SEC_71 = ("7.1 Diuretics Initiation of lisinopril in patients on diuretics may result in excessive reduction of "
          "blood pressure. Potassium-sparing diuretics (spironolactone, amiloride, triamterene, and others) can "
          "increase the risk of hyperkalemia.")
SEC_55 = ("5.5 Hyperkalemia Serum potassium should be monitored periodically in patients receiving lisinopril. "
          "Risk factors for the development of hyperkalemia include renal insufficiency, diabetes mellitus.")
E25 = "Lisinopril can cause hyperkalemia in patients with renal insufficiency [Source 2]."


def test_markers_function_words_and_generic_verbs_are_not_content():
    assert set(content_terms("Lisinopril can cause hyperkalemia in patients [Source 2].")) == {"lisinopril", "hyperkalemia"}


def test_a_fact_from_another_retrieved_section_is_misattributed():
    assert misattributed_terms(E25, [SEC_71], [SEC_55]) == ["insufficiency", "renal"]
    assert misattributed_terms(E25, [SEC_55], [SEC_71]) == []


def test_wording_found_in_no_retrieved_source_is_left_to_the_verifier():
    # A paraphrase (or content no source has) is not a misattribution; the verifier and strength checks judge it.
    assert uncited_terms("Lisinopril can cause hyperkalemia in kidney failure.", [SEC_55]) == ["failure", "kidney"]
    assert misattributed_terms("Lisinopril can cause hyperkalemia in kidney failure.", [SEC_55], [SEC_71]) == []


def test_one_other_source_must_hold_every_missing_word():
    # A correct paraphrase of 5.5: "blood" is in 7.1 ("blood pressure"), but "kidney" and "impairment" are in neither.
    paraphrase = "Lisinopril can raise blood potassium in people with kidney impairment."
    assert uncited_terms(paraphrase, [SEC_55]) == ["blood", "impairment", "kidney"]
    assert misattributed_terms(paraphrase, [SEC_55], [SEC_71]) == []
    # The words are split across two other sources, so neither alone accounts for the gap.
    assert misattributed_terms(E25, [SEC_71], ["Renal clearance.", "Insufficiency."]) == []


def test_known_limit_a_lone_common_word_found_elsewhere_still_withholds():
    # Correctly cited to 5.5, but its one missing word "blood" is in 7.1: a word screen cannot tell this from a
    # one-word misattribution ("in diabetes" cited to 7.1), so it fails safe. Documented, not fixed.
    correct = "Lisinopril can cause hyperkalemia in renal insufficiency, raising blood potassium."
    assert misattributed_terms(correct, [SEC_55], [SEC_71]) == ["blood"]
    assert misattributed_terms("Lisinopril can cause hyperkalemia in diabetes.", [SEC_71], [SEC_55]) == ["diabetes"]


def test_uncited_sources_never_vouch_for_a_statement():
    # Support is not borrowed: with no cited text the statement fails, whatever the other sources say.
    assert citation_alignment_violation(E25, [], [SEC_55, SEC_71]) == "the statement cites no retrieved source"


def test_a_word_inside_another_word_does_not_count():
    assert uncited_terms("Lisinopril affects renal function.", ["Lisinopril affects adrenal function."]) == ["renal"]


def test_a_similar_drug_name_does_not_count():
    assert misattributed_terms("Enalapril can cause hyperkalemia.", [SEC_55], ["Enalapril label section."]) == ["enalapril"]


def test_inflections_match_their_base_form():
    cited = ["Monitor the serum potassium frequently, or consider discontinuing the diuretic."]
    assert uncited_terms("Serum potassium should be monitored; diuretics can be discontinued.", cited) == []


def test_several_cited_sources_are_judged_together():
    both = "Hyperkalemia with renal insufficiency, and excessive reduction of blood pressure with diuretics."
    assert misattributed_terms(both, [SEC_55], [SEC_71]) == ["blood", "diuretics", "excessive", "pressure", "reduction"]
    assert misattributed_terms(both, [SEC_55, SEC_71], []) == []


@pytest.mark.parametrize(("statement", "cited", "others", "expected"), [
    ("Lisinopril can cause hyperkalemia in diabetes mellitus.", [SEC_71], [SEC_55],
     "attribution not verified: the cited source does not mention, though another retrieved source does: "
     "diabetes, mellitus"),
    ("Lisinopril can cause hyperkalemia in diabetes mellitus.", [SEC_55], [SEC_71], None),
])
def test_the_violation_names_the_misplaced_words_as_written(statement, cited, others, expected):
    assert citation_alignment_violation(statement, cited, others) == expected


def test_unicode_hyphens_from_the_model_match_the_source_spelling():
    # "potassium‑sparing" (U+2011) is the source's "potassium-sparing", not "potassium" and "sparing".
    assert uncited_terms("Potassium‑sparing diuretics increase hyperkalemia.", [SEC_71]) == []
