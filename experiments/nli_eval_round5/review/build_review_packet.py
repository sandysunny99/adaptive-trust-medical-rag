"""Round 5: build the independent-review packet for NLI_EVAL_SET_V1 (the frozen set is only read).

Two stages, so the reviewer is not anchored by the AI-authored labels or any model output:
  1. REVIEW_STAGE1_BLIND_V1.csv: evidence and claim only; the reviewer records a label and rationale.
  2. REVIEW_STAGE2_ADJUDICATION_V1.csv: the proposed label, its rationale and provenance, opened only
     after stage 1 is complete, with columns for agreement, adjudication and its rationale.
No model score or predicted label appears in either file. See REVIEW_PROTOCOL_V1.md.

    uv run python experiments/nli_eval_round5/review/build_review_packet.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVAL = ROOT / "experiments" / "nli_eval_round4" / "NLI_EVAL_SET_V1.jsonl"
FROZEN_SHA256 = "bd23fe488df4be20bfdb9273ba8c8942c3043955dcd4254d06b0cee3d335f4ff"
OUT = Path(__file__).resolve().parent
LABELS = "ENTAILMENT | NEUTRAL | CONTRADICTION | AMBIGUOUS | INSUFFICIENT_CONTEXT"


def main() -> int:
    raw = EVAL.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SHA256:
        raise SystemExit("NLI_EVAL_SET_V1 does not match its frozen hash; refusing to build a packet from it")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    with (OUT / "REVIEW_STAGE1_BLIND_V1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["example_id", "split", "source_url", "section", "source_chunk_id", "premise_sha256",
                    "evidence_text", "claim", "reviewer_id", f"reviewer_label ({LABELS})", "reviewer_rationale",
                    "reviewed_at (YYYY-MM-DD)"])
        for r in rows:
            w.writerow([r["id"], r["split"], r["source_url"], r["section"], r["source_chunk_id"], r["premise_sha256"],
                        r["premise"], r["hypothesis"], "", "", "", ""])
    with (OUT / "REVIEW_STAGE2_ADJUDICATION_V1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["example_id", "proposed_label", "proposed_rationale", "proposed_category", "label_origin",
                    "review_status", "reviewer_label (copy from stage 1)", "agrees (yes/no)", "adjudicated_label",
                    "adjudicator_id", "adjudication_rationale", "adjudicated_at (YYYY-MM-DD)"])
        for r in rows:
            w.writerow([r["id"], r["expected_nli_label"], r["reason"], r["category"], r["label_origin"],
                        r["review_status"], "", "", "", "", "", ""])
    print(f"wrote 2 sheets for {len(rows)} examples; frozen set unchanged ({FROZEN_SHA256[:12]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
