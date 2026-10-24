"""SPL (DailyMed label XML) section text for the relationship-candidate builders.

text_of() in scripts/build_rel_live_0003_candidate.py (reused by the REL-LIVE-0004 and
FOOD-0001 builders) used to join every text node with nothing between them, so two
paragraphs, list items or table cells with no whitespace between their tags ran together
("...bleeding.Monitor INR..."), and a <br/> joined the words on either side. Block-level
narrative elements now end a run of text; inline markup such as <content> still joins as
written, and words the publisher ran together inside one text node stay as published:
the extractor never invents a space. Synthetic XML only; no network.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from lxml import etree

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
V3 = "urn:hl7-org:v3"


@pytest.fixture(scope="module")
def text_of():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "build_rel_live_0003_candidate", SCRIPTS / "build_rel_live_0003_candidate.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPTS))
    return module.text_of


def spl(body: str):
    return etree.fromstring(f'<section xmlns="{V3}">{body}</section>')


@pytest.mark.parametrize(
    "body, expected",
    [
        (
            "<text><paragraph>Bleeding was reported.</paragraph><paragraph>Monitor patients."
            "</paragraph></text>",
            "Bleeding was reported. Monitor patients.",
        ),
        (
            "<text><paragraph>first line<br/>second line</paragraph></text>",
            "first line second line",
        ),
        (
            "<text><list><item>aspirin</item><item>heparin</item></list></text>",
            "aspirin heparin",
        ),
        (
            "<text><table><tbody><tr><td>Drug</td><td>Effect</td></tr><tr><td>warfarin</td>"
            "<td>bleeding</td></tr></tbody></table></text>",
            "Drug Effect warfarin bleeding",
        ),
        (
            "<title>7.3 Drugs</title><text><paragraph>Text.</paragraph></text>",
            "7.3 Drugs Text.",
        ),
    ],
    ids=["paragraphs", "line-break", "list-items", "table-cells", "title-and-text"],
)
def test_block_elements_do_not_run_together(text_of, body, expected):
    assert text_of(spl(body)) == expected


def test_inline_markup_and_tail_text_join_as_written(text_of):
    body = (
        "<text><paragraph>Use <content styleCode='bold'>war</content>farin with care"
        "<sup>1</sup>, and see <content>section 7</content>.</paragraph></text>"
    )
    assert text_of(spl(body)) == "Use warfarin with care1, and see section 7."


def test_nested_sections_are_read_once_in_document_order(text_of):
    body = (
        "<title>7 DRUG INTERACTIONS</title><text><paragraph>Intro.</paragraph></text>"
        "<component><section><title>7.1 Diuretics</title><text><paragraph>Nested."
        "</paragraph></text></section></component>"
    )
    assert text_of(spl(body)) == "7 DRUG INTERACTIONS Intro. 7.1 Diuretics Nested."


def test_whitespace_is_collapsed_to_single_spaces(text_of):
    body = "<text>\n   <paragraph>  a\n\tb   </paragraph>\n</text>"
    assert text_of(spl(body)) == "a b"


def test_publisher_run_together_words_are_not_split(text_of):
    # DailyMed set 72ec2491-924d-460f-9510-62d624d54b59 v17 has "Ibuprofentablets" inside one
    # text node. The extractor keeps it: splitting it would put words in the label's mouth.
    body = "<text><paragraph>failed to show that Ibuprofentablets significantly</paragraph></text>"
    assert text_of(spl(body)) == "failed to show that Ibuprofentablets significantly"


def test_comments_and_processing_instructions_add_no_text(text_of):
    body = "<text><paragraph>a<!-- hidden -->b<?pi data?>c</paragraph></text>"
    assert text_of(spl(body)) == "abc"


def test_a_missing_or_empty_node_gives_no_text(text_of):
    assert text_of(None) == ""
    assert text_of(spl("")) == ""
