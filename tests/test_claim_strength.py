"""The claim-strength policy: a statement may not claim more than its source's reviewed wording."""

from __future__ import annotations

import pytest

from adaptive_trust_medical_rag.services.claim_strength import reviewed_food_lines, strength_violation

RISK_MONITOR = {"supported_claims": [{
    "text": "Potassium-containing salt substitutes are listed as a risk factor for hyperkalemia in patients "
            "receiving lisinopril, and the label advises periodic serum potassium monitoring.",
    "action": "MONITOR"}]}


@pytest.mark.parametrize("text", [
    "Potassium-containing salt substitutes are a risk factor for hyperkalemia with lisinopril [Source 1].",
    "Salt substitutes containing potassium can increase the risk of hyperkalemia; serum potassium should be "
    "monitored periodically [Source 1].",
    "Lisinopril: specific food/drink interaction; potassium-containing salt substitutes may raise potassium [Source 1].",
])
def test_wording_within_the_reviewed_strength_passes(text):
    assert strength_violation(text, [RISK_MONITOR]) is None


@pytest.mark.parametrize(("text", "why"), [
    ("Avoid potassium-containing salt substitutes while taking lisinopril.", "AVOID"),
    ("Do not use salt substitutes with lisinopril.", "AVOID"),
    ("Steer clear of potassium salt substitutes.", "AVOID"),
    ("Salt substitutes should not be used with lisinopril.", "AVOID"),
    ("Limit salt substitutes while on lisinopril.", "LIMIT"),
    ("Keep potassium intake below 2000 mg per day.", "LIMIT"),
    ("Potassium salt substitutes will cause hyperkalemia with lisinopril.", "CERTAINTY"),
    ("Use no more than one teaspoon of salt substitute.", "LIMIT"),
    ("Take lisinopril without food to avoid hyperkalemia.", "AVOID"),
    ("Stop taking lisinopril if you use salt substitutes.", "CHANGE_MEDICATION"),
    ("Follow a low-potassium diet plan with lisinopril.", "PERSONAL_PLAN"),
])
def test_overstated_wording_is_rejected(text, why):
    violation = strength_violation(text, [RISK_MONITOR])
    assert violation is not None and why in violation


def test_certainty_quantity_and_timing_need_explicit_reviewed_support():
    assert "CERTAINTY" in strength_violation("Salt substitutes always raise potassium risk.", [RISK_MONITOR])
    assert "QUANTITY" in strength_violation("Salt substitutes raise risk at 3 g a day.", [RISK_MONITOR])
    assert "TIMING" in strength_violation("Risk of hyperkalemia with food at bedtime.", [RISK_MONITOR])
    allows = {"supported_claims": [{"text": "x", "action": "MONITOR", "allows": ["TIMING"]}]}
    assert strength_violation("Monitor potassium at bedtime.", [allows]) is None


def test_a_stronger_reviewed_action_allows_stronger_wording():
    avoid = {"supported_claims": [{"text": "Avoid grapefruit juice.", "action": "AVOID"}]}
    assert strength_violation("Avoid grapefruit juice with this medicine.", [avoid]) is None
    assert "CHANGE_MEDICATION" in strength_violation("Stop the medicine if you drink grapefruit juice.", [avoid])


def test_sources_without_reviewed_wording_do_not_constrain_here():
    assert strength_violation("Avoid salt substitutes.", [{}]) is None


def test_the_released_food_lines_are_the_reviewed_wording_with_markers():
    lines = reviewed_food_lines({1: RISK_MONITOR})
    assert lines == [RISK_MONITOR["supported_claims"][0]["text"] + " [Source 1]"]


# ── Sources without reviewed wording bound a statement by their own text (round 3, 2026-10-26) ──
# With one eligible chunk (lisinopril label 7.1, no reviewed wording), the real NLI model accepted
# "Thiazide diuretics should be stopped in all patients taking lisinopril" at 0.999. The label only
# says the diuretic may be decreased or discontinued to minimise hypotension.

from adaptive_trust_medical_rag.services.claim_strength import source_text_violation  # noqa: E402

LABEL_71 = ("7.1 Diuretics Initiation of lisinopril in patients on diuretics may result in excessive reduction of "
            "blood pressure. The possibility of hypotensive effects with lisinopril can be minimized by either "
            "decreasing or discontinuing the diuretic or increasing the salt intake prior to initiation of treatment "
            "with lisinopril. If this is not possible, reduce the starting dose of lisinopril tablets. Lisinopril "
            "attenuates potassium loss caused by thiazide-type diuretics. Potassium-sparing diuretics "
            "(spironolactone, amiloride, triamterene, and others) can increase the risk of hyperkalemia. Therefore, "
            "if concomitant use of such agents is indicated, monitor the patient's serum potassium frequently.")


@pytest.mark.parametrize("statement", [
    "Thiazide diuretics should be stopped in all patients taking lisinopril [Source 1].",
    "Lisinopril must always be avoided with spironolactone [Source 1].",
    "Spironolactone will cause hyperkalemia with lisinopril [Source 1].",
])
def test_a_statement_stronger_or_more_certain_than_its_unreviewed_source_is_refused(statement):
    assert source_text_violation(statement, [LABEL_71]) is not None


@pytest.mark.parametrize("statement", [
    "Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood pressure [Source 1].",
    "Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia when used with "
    "lisinopril; monitor serum potassium frequently [Source 1].",
    "Lisinopril interacts with spironolactone, which can increase the risk of hyperkalemia [Source 1].",
    "Concomitant use of lisinopril and spironolactone can increase the risk of hyperkalemia [Source 1].",
])
def test_statements_the_label_states_pass(statement):
    assert source_text_violation(statement, [LABEL_71]) is None


# ── Population, outcome severity and timing qualifiers (round 5, 2026-10-26) ──
# With an over-entailing NLI, "in pediatric patients", "fatal" and "within 24 hours" added to a correct, correctly
# cited lisinopril statement were released: the cue lists had no class for them. A source must state each one.

@pytest.mark.parametrize(("statement", "extra"), [
    ("Hyperkalemia occurs in pediatric patients receiving lisinopril [Source 1].", "PEDIATRIC"),
    ("Hyperkalemia occurs in children receiving lisinopril [Source 1].", "PEDIATRIC"),
    ("Hyperkalemia occurs in elderly patients receiving lisinopril [Source 1].", "GERIATRIC"),
    ("Lisinopril causes hyperkalemia during pregnancy [Source 1].", "PREGNANCY"),
    ("Lisinopril causes hyperkalemia in breastfeeding women [Source 1].", "LACTATION"),
    ("Lisinopril can cause fatal hyperkalemia [Source 1].", "SEVERITY"),
    ("Hyperkalemia with lisinopril can be life-threatening [Source 1].", "SEVERITY"),
    ("Hyperkalemia occurs within 24 hours of starting lisinopril [Source 1].", "DURATION"),
    ("Hyperkalemia may appear 2 to 3 days after lisinopril is started [Source 1].", "DURATION"),
    ("Serum potassium should be checked immediately in patients receiving lisinopril [Source 1].", "TIMING"),
])
def test_population_severity_and_timing_need_the_source_to_state_them(statement, extra):
    assert extra in strength_violation(statement, [RISK_MONITOR])
    assert extra in source_text_violation(statement, [LABEL_71])


def test_a_qualifier_the_source_states_passes():
    source = "Fatal hyperkalemia has been reported in pediatric patients within 3 days of starting treatment."
    assert source_text_violation("Lisinopril can cause fatal hyperkalemia in pediatric patients [Source 1].", [source]) is None
    assert source_text_violation("Hyperkalemia was reported within 3 days in children [Source 1].", [source]) is None


@pytest.mark.parametrize("grade", ["common", "important", "serious"])
def test_the_answer_schema_severity_grades_are_not_outcome_severity_claims(grade):
    # adverse_reactions[].severity is "common | important | serious" (LIVE_APP_PROMPT_V2); the statement built
    # from it reads "... severity serious". Graded words are not in the SEVERITY class; outcomes (fatal ...) are.
    assert strength_violation(f"Lisinopril can cause hyperkalemia; severity {grade} [Source 1].", [RISK_MONITOR]) is None


def test_unicode_hyphens_from_the_model_do_not_hide_a_qualifier():
    # The live model writes U+2011 (non-breaking hyphen): "life‑threatening" must match like "life-threatening".
    assert "SEVERITY" in strength_violation("Hyperkalemia with lisinopril can be life‑threatening [Source 1].", [RISK_MONITOR])
    assert "LACTATION" in source_text_violation("Lisinopril in breast‑feeding women [Source 1].", [LABEL_71])
    assert "DURATION" in source_text_violation("Hyperkalemia appears 2–3 days after starting [Source 1].", [LABEL_71])
