"""Round 6: the frozen set and the medication probes through the full live path with the RxNorm lexicon in place.

Reuses the round-5 harness (experiments/nli_eval_round5/replay_live_policy.py) unchanged: real DailyMed sections
approved only in a temp folder, the pinned PubMedBERT-MNLI-MedNLI, every live gate, alignment on. Adds probes of the
lexicon's recognition boundary. The probes are diagnostics, not part of NLI_EVAL_SET_V1 and not labels:

  P01-P06  as in round 5 (P01 enalapril, P05/P06 furosemide cited to 5.5 / 7.1)
  P07      metamizole (dipyrone's international name; the lexicon holds RxNorm names only) cited to 7.1
  P08      an invented name with no drug suffix cited to 7.1
  P09      dipyrone (in the lexicon) cited to 7.1
  *-single P06-P09 with section 7.1 retrieved alone

Each record adds the claim's medication findings (identity, status, named by a cited source).

    TESTING= HF_HUB_OFFLINE=1 uv run python experiments/nli_eval_round6/replay_round6.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "nli_eval_round5"))

import replay_live_policy as r5  # noqa: E402

from adaptive_trust_medical_rag.normalization.medication_lexicon import default_lexicon  # noqa: E402
from adaptive_trust_medical_rag.verification.canonical_identity import RequestDrugMap, medication_findings  # noqa: E402
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2  # noqa: E402

OUT = ROOT / "experiments" / "nli_eval_round6" / "results" / "LIVE_POLICY_REPLAY_R6.json"
NEW_PROBES = [{"id": "P07", "section": "7.1", "hypothesis": "Metamizole can cause hyperkalemia in patients with renal insufficiency."},
              {"id": "P08", "section": "7.1", "hypothesis": "Zorbitrex can cause hyperkalemia in patients with renal insufficiency."},
              {"id": "P09", "section": "7.1", "hypothesis": "Dipyrone can cause hyperkalemia in patients with renal insufficiency."}]
# The same claims with section 7.1 retrieved alone: P07 and P08 were withheld above only because the uncited 5.5's
# neutral score (0.99) outweighed the cited entailment (0.80) in the verifier's aggregate. Alone, nothing does.
NEW_PROBES += [dict(p, id=p["id"] + "-single", retrieved=["7.1"]) for p in (
    {"id": "P06", "section": "7.1", "hypothesis": "Furosemide can cause hyperkalemia in patients with renal insufficiency."},
    *NEW_PROBES)]


def main() -> int:
    examples = [json.loads(line) for line in r5.EVAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    verifier = ClaimVerifierV2()
    with tempfile.TemporaryDirectory() as tmp:
        loaded = r5.load_state(Path(tmp))
        rows = [{"id": ex["id"], "split": ex["split"], "category": ex["category"],
                 "expected_app_outcome": ex["expected_app_outcome"], "result": r5.replay(ex, loaded, verifier)}
                for ex in examples]
        probes = [{"id": p["id"], "result": r5.replay(p, loaded, verifier)} for p in r5.PROBES + NEW_PROBES]
        by_id = {e["chunk_id"]: e for e in loaded.relationship_store.evidence}
    # The round-5 record has the guard's verdict but not its per-mention findings; recompute them with the live
    # function on the same inputs (claim text, confirmed drugs, cited chunk text and verified source title).
    lexicon = default_lexicon()
    for record in rows + probes:
        res = record["result"]
        cited = by_id[res["cited_chunk"]]
        confirmed = RequestDrugMap({d.lower(): r5.RXCUI[d.lower()] for d in res["drugs"]})
        res["medication_mentions"] = medication_findings(
            res["claim"], confirmed, [cited["text"], (cited.get("source_identity") or {}).get("title") or ""], lexicon)

    released = [r for r in rows if r["result"]["outcome"] == "RELEASE"]
    summary = {"released": len(released),
               "false_releases": [r["id"] for r in released if r["expected_app_outcome"] != "RELEASE"],
               "false_withholds": [r["id"] for r in rows if r["expected_app_outcome"] == "RELEASE"
                                   and r["result"]["outcome"] != "RELEASE"],
               "probes": {p["id"]: [p["result"]["outcome"], p["result"]["withheld_by"],
                                    p["result"]["medication_identity"]] for p in probes}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"dataset": "NLI_EVAL_SET_V1", "dataset_sha256": hashlib.sha256(r5.EVAL.read_bytes()).hexdigest(),
                               "model": f"{verifier.model_id}@{verifier.revision}", "labels": "UNREVIEWED",
                               "probes_note": "diagnostic probes, not part of NLI_EVAL_SET_V1 and not labels",
                               "summary": summary, "examples": rows, "probes": probes}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
