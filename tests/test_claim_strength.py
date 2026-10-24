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
