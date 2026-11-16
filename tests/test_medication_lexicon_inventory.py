"""The frozen recognition inventory (tests/fixtures/medication_lexicon/INVENTORY_V1.json) against the pinned lexicon."""

import json
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.normalization.medication_lexicon import default_lexicon

INVENTORY = json.loads((Path(__file__).parent / "fixtures" / "medication_lexicon" / "INVENTORY_V1.json")
                       .read_text(encoding="utf-8"))


def test_the_inventory_is_for_the_pinned_release():
    assert INVENTORY["release"] == default_lexicon().release


@pytest.mark.parametrize("case", INVENTORY["cases"], ids=[f"{c['category']}: {c['text']}" for c in INVENTORY["cases"]])
def test_each_inventory_case_is_recognised_exactly_as_recorded(case):
    found = [[m.text, m.rxcui, m.tty] for m in default_lexicon().mentions(case["text"])]
    assert found == case["expected"]
