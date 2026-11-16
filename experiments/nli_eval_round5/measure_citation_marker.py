"""Round 5: does the "[Source N]" marker in the NLI hypothesis change the live model's scores? (measurement only)

ClaimVerifierV2 scores each decomposed clause as written, marker included ("... insufficiency [Source 2]."). This
scores that exact hypothesis and the same text with only the marker removed, against the cited section and every
other retrieved section, with the live model at its pinned revision; premise, tokenizer and pipeline are identical.
The examples are NLI_EVAL_SET_V1 (labels UNREVIEWED) and the round-5 replay probes, cited as in the replay. Nothing
here changes the application: a model-input normalisation would be chosen on development or reviewed data, not on
the frozen evaluation split this measures.

    TESTING= HF_HUB_OFFLINE=1 uv run python experiments/nli_eval_round5/measure_citation_marker.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.pop("TESTING", None)  # the real model, not the keyword stand-in

from replay_live_policy import EVAL, FIX, NAMES, PROBES, SEC  # noqa: E402

from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2, decompose_into_claims  # noqa: E402

OUT = ROOT / "experiments" / "nli_eval_round5" / "results" / "CITATION_MARKER_EFFECT_V1.json"
MARKER = re.compile(r"\s*\[Source\s+\d+\]")


def section_texts() -> dict[str, str]:
    texts = {}
    for fixture in ("food_0001_candidate", "rel_live_0003_candidate", "rel_live_0004_candidate"):
        data = json.loads((FIX / fixture / NAMES[1]).read_text(encoding="utf-8"))
        for item in data["evidence"] if isinstance(data, dict) else data:
            texts[item["chunk_id"]] = item["text"]
    return texts


def verdict(scores: dict[str, float]) -> str:
    return max(scores, key=scores.get)


def main() -> int:
    examples = [json.loads(line) for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()] + PROBES
    texts = section_texts()
    verifier = ClaimVerifierV2()
    rows = []
    for ex in examples:
        retrieved = [SEC["5.5"], SEC["7.1"]] if ex["section"] in ("5.5", "7.1") else [SEC["7.3"]]
        cite = retrieved.index(SEC[ex["section"]]) + 1
        (clause,) = decompose_into_claims(f"{ex['hypothesis'].rstrip('.')} [Source {cite}].")
        bare = MARKER.sub("", clause.text)
        chunks = []
        for n, chunk_id in enumerate(retrieved, start=1):
            with_marker = {k: round(v, 4) for k, v in verifier._evaluate_pair(texts[chunk_id], clause.text).items()}
            without = {k: round(v, 4) for k, v in verifier._evaluate_pair(texts[chunk_id], bare).items()}
            chunks.append({"chunk_id": chunk_id, "role": "cited" if n == cite else "uncited",
                           "with_marker": with_marker, "without_marker": without,
                           "verdict_with": verdict(with_marker), "verdict_without": verdict(without),
                           "entailment_delta": round(without["entailment"] - with_marker["entailment"], 4)})
        rows.append({"id": ex["id"], "split": ex.get("split", "probe"), "category": ex.get("category", "probe"),
                     "expected_app_outcome": ex.get("expected_app_outcome"), "hypothesis_scored": clause.text,
                     "hypothesis_without_marker": bare, "chunks": chunks})

    cited = [c for r in rows for c in r["chunks"] if c["role"] == "cited"]
    flips = [{"id": r["id"], "role": c["role"], "with": c["verdict_with"], "without": c["verdict_without"],
              "expected_app_outcome": r["expected_app_outcome"]}
             for r in rows for c in r["chunks"] if c["verdict_with"] != c["verdict_without"]]
    deltas = sorted(abs(c["entailment_delta"]) for r in rows for c in r["chunks"])
    summary = {
        "pairs_scored": len(deltas), "examples": len(rows),
        "verdict_flips": flips,
        "cited_verdict_flips": sum(1 for c in cited if c["verdict_with"] != c["verdict_without"]),
        "abs_entailment_delta": {"median": deltas[len(deltas) // 2], "max": deltas[-1],
                                 "over_0.1": sum(d > 0.1 for d in deltas), "over_0.3": sum(d > 0.3 for d in deltas)},
    }
    OUT.write_text(json.dumps({"dataset": "NLI_EVAL_SET_V1 + round-5 replay probes",
                               "dataset_sha256": hashlib.sha256(EVAL.read_bytes()).hexdigest(),
                               "model": f"{verifier.model_id}@{verifier.revision}", "labels": "UNREVIEWED",
                               "summary": summary, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
