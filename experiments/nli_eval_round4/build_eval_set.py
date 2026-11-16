"""Build the round-4 NLI evaluation set (2026-10-26 audit) from real DailyMed label text.

Premises are the exact evidence chunks of the repository's candidate fixtures (tests/fixtures/*_candidate,
real SPL text captured from DailyMed). Nothing here is production evidence and nothing is approved.
Every expected label was written by the audit author (an AI assistant) and is UNREVIEWED: a
development reference for comparing models, not clinician-validated ground truth. Round-3 observed
scores are copied only where the round-3 report recorded them.

Split by source document to limit leakage: warfarin label section 7.3 is the dev split (harness and
label-mapping checks); lisinopril label sections 5.5 and 7.1 are the frozen evaluation split.
Run from the repository root:  python experiments/nli_eval_round4/build_eval_set.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FIX = ROOT / "tests" / "fixtures"

L71 = "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1"
L55 = "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5"
W73 = "DAILYMED-884CDBF6-SPL-V8-SEC-7.3"
E, N, C = "ENTAILMENT", "NEUTRAL", "CONTRADICTION"
REL, WH = "RELEASE", "WITHHOLD"

# (id, chunk, hypothesis, expected label, category, expected app outcome, reason, round-3 observed or None)
EXAMPLES = [
    # dev split: warfarin label 7.3
    ("D01", W73, "Ibuprofen can increase the risk of bleeding when used with warfarin.", E, "A_true_support_pair", REL,
     "Table 3 lists ibuprofen among drugs that increase bleeding risk with warfarin.", None),
    ("D02", W73, "Patients receiving aspirin with warfarin should be closely monitored.", E, "A_true_support_paraphrase", REL,
     "Closely monitor patients receiving any such drug with warfarin; aspirin is listed.", None),
    ("D03", W73, "Warfarin should never be used with ibuprofen.", N, "C_overstatement_mandatory", WH,
     "Label advises close monitoring, not prohibition.", None),
    ("D04", W73, "Ibuprofen always causes bleeding in patients taking warfarin.", N, "C_overstatement_universal", WH,
     "Label states increased risk, not certainty.", None),
    ("D05", W73, "Acetaminophen increases the risk of bleeding with warfarin.", N, "B_absent_claim", WH,
     "Acetaminophen is not in the table.", None),
    ("D06", W73, "Ibuprofen causes stomach ulcers.", N, "B_other_outcome", WH, "Section does not discuss ulcers.", None),
    ("D07", W73, "Bleeding risk is decreased when warfarin is used with naproxen.", C, "C_contradiction", WH,
     "Label says risk is increased.", None),
    ("D08", W73, "Warfarin should be stopped in all patients taking sertraline.", N, "C_overstatement_action", WH,
     "Label advises monitoring, not stopping.", None),
    # frozen eval split: lisinopril label 7.1 and 5.5
    ("E01", L55, "Serum potassium should be monitored periodically in patients receiving lisinopril.", E,
     "A_true_support_direct", REL, "Verbatim first sentence of 5.5.", None),
    ("E02", L55, "Lisinopril can cause hyperkalemia.", E, "A_true_support_paraphrase", REL,
     "RAS inhibitors can cause hyperkalemia; lisinopril is the subject of the label.", None),
    ("E03", L55, "Diabetes mellitus is a risk factor for hyperkalemia in patients receiving lisinopril.", E,
     "A_true_support_direct", REL, "Listed risk factor.", None),
    ("E04", L71, "Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood pressure.", E,
     "A_true_support_direct", REL, "Verbatim 7.1.", None),
    ("E05", L71, "Potassium-sparing diuretics such as spironolactone can increase the risk of hyperkalemia with lisinopril.", E,
     "A_true_support_pair", REL, "7.1 lists spironolactone among potassium-sparing diuretics that increase hyperkalemia risk.", None),
    ("E06", L71, "Lisinopril interacts with spironolactone, increasing risk of hyperkalemia.", E,
     "D_known_r3_false_withholding", REL, "Round-3 known false withholding (INSUFFICIENT via another chunk's neutral).",
     {"SEC-7.1": {"entailment": 0.998}, "SEC-5.5": {"neutral": 0.999}}),
    ("E07", L71, "Lisinopril attenuates potassium loss caused by thiazide-type diuretics.", E,
     "D_known_r3_false_withholding", REL, "Verbatim 7.1; round-3 AMBIGUOUS via false contradiction with 5.5.",
     {"SEC-7.1": {"entailment": 1.0}, "SEC-5.5": {"contradiction": 0.977}}),
    ("E08", L55, "Lisinopril attenuates potassium loss caused by thiazide-type diuretics.", N,
     "D_known_r3_false_contradiction", WH, "5.5 does not address thiazide potassium loss; round-3 model said CONTRADICTION 0.977.",
     {"SEC-5.5": {"contradiction": 0.977}}),
    ("E09", L71, "Excessive reduction of blood pressure when lisinopril is initiated in patients on diuretics.", E,
     "D_known_r3_false_withholding", REL, "Paraphrase of 7.1; round-3 INSUFFICIENT in one run.", None),
    ("E10", L71, "The hypotensive effect of starting lisinopril can be minimized by increasing salt intake before treatment.", E,
     "A_true_support_paraphrase", REL, "7.1 lists increasing salt intake.", None),
    ("E11", L71, "Serum potassium should be monitored frequently when potassium-sparing diuretics are used with lisinopril.", E,
     "A_true_support_paraphrase", REL, "7.1 final sentence.", None),
    ("E12", L55, "Lisinopril should be stopped immediately in all patients.", N, "D_known_r3_false_acceptance", WH,
     "Not stated anywhere; round-3 model gave 7.1 entailment 0.991 and 5.5 neutral 1.0.",
     {"SEC-7.1": {"entailment": 0.991}, "SEC-5.5": {"neutral": 1.0}}),
    ("E13", L71, "Lisinopril should be stopped immediately in all patients.", N, "D_known_r3_false_acceptance", WH,
     "Not stated; round-3 7.1 entailment 0.991.", {"SEC-7.1": {"entailment": 0.991}}),
    ("E14", L71, "Lisinopril causes kidney failure in all patients.", N, "D_known_r3_false_acceptance", WH,
     "Not stated; round-3 7.1 entailment 0.568.", {"SEC-7.1": {"entailment": 0.568}}),
    ("E15", L71, "Thiazide diuretics should be stopped in all patients taking lisinopril.", N, "D_known_r3_false_acceptance", WH,
     "Label: the diuretic may be decreased or discontinued to minimize hypotension, not in all patients; round-3 0.999.",
     {"SEC-7.1": {"entailment": 0.999}}),
    ("E16", L71, "Spironolactone is contraindicated with lisinopril.", N, "C_overstatement_mandatory", WH,
     "Label advises potassium monitoring, not contraindication.", None),
    ("E17", L71, "Lisinopril reduces the risk of hyperkalemia.", C, "C_contradiction", WH,
     "Label: hyperkalemia risk is increased with potassium-sparing diuretics.", None),
    ("E18", L71, "Lisinopril must never be combined with any diuretic.", C, "C_overstatement_universal", WH,
     "Label describes how to combine with diuretics safely.", None),
    ("E19", L71, "Initiation of lisinopril in patients on diuretics will always cause excessive reduction of blood pressure.", N,
     "C_may_to_always", WH, "Label says may.", None),
    ("E20", L71, "Spironolactone must always be stopped before lisinopril is started.", N, "C_overstatement_action", WH,
     "Not stated.", None),
    ("E21", L71, "Lisinopril should be taken with grapefruit juice.", N, "B_absent_claim", WH, "Not in section.", None),
    ("E22", L71, "Lisinopril is safe with potassium supplements.", N, "B_absent_claim", WH,
     "7.1 does not address supplements; 5.5 lists them as a risk factor.", None),
    ("E23", L55, "Lisinopril is safe with potassium supplements.", C, "C_contradiction", WH,
     "5.5 lists potassium supplements as a hyperkalemia risk factor.", None),
    ("E24", L55, "Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood pressure.", N,
     "A_wrong_section", WH, "True statement, but 5.5 does not support it (7.1 does).", None),
    ("E25", L71, "Lisinopril can cause hyperkalemia in patients with renal insufficiency.", N, "A_wrong_section", WH,
     "Supported by 5.5, not by 7.1.", None),
    ("E26", L71, "Spironolactone causes gynecomastia.", N, "B_other_outcome", WH, "Not in section.", None),
    ("E27", L71, "Amlodipine increases the risk of hyperkalemia with lisinopril.", N, "B_other_pair", WH,
     "Amlodipine not mentioned.", None),
    ("E28", L71, "Initiating lisinopril in patients taking spironolactone may cause excessive reduction of blood pressure.", N,
     "B_class_to_specific", WH, "The hypotension statement is about diuretics generally; observed round-3 extrapolation.", None),
    ("E29", L55, "Potassium-containing salt substitutes are a risk factor for hyperkalemia in patients receiving lisinopril.", E,
     "A_true_support_direct", REL, "Listed risk factor.", None),
    ("E30", L55, "Patients receiving lisinopril must avoid all potassium-containing salt substitutes.", N,
     "C_overstatement_mandatory", WH, "Risk factor, not prohibition.", None),
    ("E31", L55, "Serum potassium should be monitored daily in patients receiving lisinopril.", N, "C_timing_change", WH,
     "Label says periodically.", None),
    ("E32", L55, "Hyperkalemia occurs in all patients receiving lisinopril.", N, "C_overstatement_universal", WH,
     "Label: can cause.", None),
    ("E33", L71, "Reducing the starting dose of lisinopril tablets is an option when the diuretic cannot be decreased or discontinued.", E,
     "A_true_support_paraphrase", REL, "7.1: If this is not possible, reduce the starting dose.", None),
    ("E34", L71, "The starting dose of lisinopril should always be 2.5 mg in patients on diuretics.", N, "C_quantity_change", WH,
     "No dose given in 7.1.", None),
]


def chunks() -> dict[str, dict]:
    out = {}
    for name in ("rel_live_0003_candidate", "rel_live_0004_candidate", "food_0001_candidate"):
        for item in json.loads((FIX / name / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").read_text(encoding="utf-8")):
            out[item["chunk_id"]] = item
    return out


def main() -> None:
    by_id = chunks()
    rows = []
    for ex_id, chunk_id, hypothesis, label, category, outcome, reason, observed in EXAMPLES:
        item = by_id[chunk_id]
        rows.append({
            "id": ex_id,
            "split": "dev" if ex_id.startswith("D") else "frozen_eval",
            "source_chunk_id": chunk_id,
            "source_url": item["document_url"],
            "section": item["text"].split(" ", 1)[0],
            "premise": item["text"],
            "premise_sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
            "hypothesis": hypothesis,
            "expected_nli_label": label,
            "category": category,
            "expected_app_outcome": outcome,
            "label_origin": "audit_author_ai",
            "review_status": "UNREVIEWED",
            "reason": reason,
            "round3_observed_scores": observed,
        })
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    (OUT / "NLI_EVAL_SET_V1.jsonl").write_bytes(data)
    manifest = {
        "dataset": "NLI_EVAL_SET_V1",
        "file": "NLI_EVAL_SET_V1.jsonl",
        "sha256": hashlib.sha256(data).hexdigest(),
        "examples": len(rows),
        "splits": {s: sum(r["split"] == s for r in rows) for s in ("dev", "frozen_eval")},
        "labels": {lab: sum(r["expected_nli_label"] == lab for r in rows) for lab in (E, N, C)},
        "label_review": ("UNREVIEWED: written by the audit author (an AI assistant). Not clinician-validated; "
                         "independent adjudication is required before these labels decide a model selection."),
        "frozen": "2026-10-26, before any candidate model was run; not edited after candidate results.",
    }
    (OUT / "NLI_EVAL_SET_V1_MANIFEST.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
