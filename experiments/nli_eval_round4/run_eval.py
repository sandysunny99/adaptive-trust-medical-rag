"""Offline comparison of NLI models on NLI_EVAL_SET_V1 (2026-10-26 audit, round 4).

Evaluation only: nothing here changes the application's verifier, its default model or any gate.
Models are loaded from the local Hugging Face cache at pinned revisions (HF_HUB_OFFLINE=1); no text
is sent to any service.

Setting A (isolated pairs): one premise (the exact label section) and one hypothesis per example,
compared with the frozen, UNREVIEWED expected label.
Setting B (verifier replay): the same claims, each citing its own section as [Source N], replayed
through the application's ClaimVerifierV2 decision logic and its source-text overstatement bound,
with only the classifier swapped inside this harness. The lisinopril examples see both lisinopril
sections as evidence (as the live pipeline did); the warfarin examples see section 7.3 alone.

Run from the repository root:
  TESTING= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run python experiments/nli_eval_round4/run_eval.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.pop("TESTING", None)  # the real classifier, never the keyword stub

from transformers import AutoTokenizer, pipeline  # noqa: E402

from adaptive_trust_medical_rag.services.claim_strength import source_text_violation  # noqa: E402
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import (  # noqa: E402
    ClaimVerifierV2,
    EvidenceChunk,
    FinalSupportState,
)

MODELS = [
    ("baseline", "pritamdeka/PubMedBERT-MNLI-MedNLI", "f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab"),
    ("biolinkbert_mednli", "cnut1648/biolinkbert-mednli", "f9f4a9d1e046a0e6574feef938f1308cecaebbd5"),
    ("biolinkbert_large_mnli_snli", "cnut1648/biolinkbert-large-mnli-snli", "89029f481c3c6f49bae0ba0cdb148d9b21847ae6"),
]
BLOCKED = [("ygivenx/modernbert-base-mednli", "7b0ef2489b155f8a53bdd7d56e4ecc9ad9c7b174",
            "gated repository: HTTP 401 without a Hugging Face account that accepted its terms")]
LABELS = ("ENTAILMENT", "NEUTRAL", "CONTRADICTION")


def load_set() -> list[dict]:
    manifest = json.loads((HERE / "NLI_EVAL_SET_V1_MANIFEST.json").read_text(encoding="utf-8"))
    raw = (HERE / manifest["file"]).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(raw).hexdigest() == manifest["sha256"], "evaluation set changed after freezing"
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def classifier(model_id: str, revision: str):
    clf = pipeline("text-classification", model=model_id, revision=revision, top_k=None)
    names = {i: v.lower() for i, v in clf.model.config.id2label.items()}
    assert sorted(names.values()) == ["contradiction", "entailment", "neutral"], names
    return clf, AutoTokenizer.from_pretrained(model_id, revision=revision)


def scores(clf, premise: str, hypothesis: str) -> dict[str, float]:
    out = clf({"text": premise, "text_pair": hypothesis})
    out = out[0] if isinstance(out[0], list) else out
    return {d["label"].upper(): float(d["score"]) for d in out}


def metrics(rows: list[dict], key: str) -> dict:
    cm = {g: Counter() for g in LABELS}
    for r in rows:
        cm[r["expected_nli_label"]][r[key]] += 1
    per = {}
    for lab in LABELS:
        tp = cm[lab][lab]
        pred = sum(cm[g][lab] for g in LABELS)
        gold = sum(cm[lab].values())
        p = tp / pred if pred else None
        rc = tp / gold if gold else None
        f1 = 2 * p * rc / (p + rc) if p and rc else 0.0
        per[lab] = {"precision": p, "recall": rc, "f1": f1, "support": gold}
    acc = sum(cm[lab][lab] for lab in LABELS) / len(rows)
    unsupported = [r for r in rows if r["expected_nli_label"] != "ENTAILMENT"]
    supported = [r for r in rows if r["expected_nli_label"] == "ENTAILMENT"]
    fa = [r["id"] for r in unsupported if r[key] == "ENTAILMENT"]
    fw = [r["id"] for r in supported if r[key] != "ENTAILMENT"]
    return {"n": len(rows), "accuracy": acc, "macro_f1": sum(v["f1"] for v in per.values()) / 3, "per_class": per,
            "confusion": {g: dict(cm[g]) for g in LABELS},
            "false_acceptance": {"count": len(fa), "of": len(unsupported), "ids": fa},
            "false_withholding": {"count": len(fw), "of": len(supported), "ids": fw}}


def _strip_markers(text: str) -> str:
    import re
    return re.sub(r"\s*\[Source\s+\d+\]", "", text).strip()


def replay(verifier: ClaimVerifierV2, rows: list[dict], premises: dict[str, str]) -> list[dict]:
    """Setting B: the application's decision logic with this classifier."""
    lis = ["DAILYMED-34EBEEA1-SPL-V12-SEC-7.1", "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5"]
    out = []
    for r in rows:
        ids = lis if r["source_chunk_id"] in lis else [r["source_chunk_id"]]
        evidence = [EvidenceChunk(chunk_id=cid, text=premises[cid], source_authority=0.95, citation_index=i)
                    for i, cid in enumerate(ids, start=1)]
        n = ids.index(r["source_chunk_id"]) + 1
        claim = f"{r['hypothesis'].rstrip('.')} [Source {n}]."
        judgments = verifier.verify(claim, evidence).judgments
        state = judgments[0].support_state if judgments else FinalSupportState.INSUFFICIENT_EVIDENCE
        bound = source_text_violation(claim, [premises[r["source_chunk_id"]]])
        released = state == FinalSupportState.SUPPORTED and bound is None
        out.append({"id": r["id"], "state": state.value, "strength_bound": bound,
                    "outcome": "RELEASE" if released else "WITHHOLD", "expected": r["expected_app_outcome"]})
    return out


def main() -> None:
    rows = load_set()
    premises = {r["source_chunk_id"]: r["premise"] for r in rows}
    results = {"dataset_sha256": json.loads((HERE / "NLI_EVAL_SET_V1_MANIFEST.json").read_text())["sha256"],
               "blocked_models": [{"model": m, "revision": rev, "reason": why} for m, rev, why in BLOCKED],
               "models": {}}
    for name, model_id, revision in MODELS:
        clf, tok = classifier(model_id, revision)
        per_example = []
        for r in rows:
            t0 = time.perf_counter()
            s = scores(clf, r["premise"], r["hypothesis"])
            ms = (time.perf_counter() - t0) * 1000
            n_tokens = len(tok(r["premise"], r["hypothesis"])["input_ids"])
            per_example.append({**{k: r[k] for k in ("id", "split", "category", "expected_nli_label")},
                                "scores": {k: round(v, 4) for k, v in s.items()},
                                "predicted": max(s, key=s.get), "latency_ms": round(ms, 1),
                                "tokens": n_tokens, "truncated": n_tokens > tok.model_max_length})
        verifier = ClaimVerifierV2()
        verifier.classifier = clf
        verifier.id2label = clf.model.config.id2label
        verifier.label_map = {v.lower(): v.lower() for v in verifier.id2label.values()}
        replayed = replay(verifier, rows, premises)
        # Setting B-marker: the same replay with the [Source N] marker kept out of the NLI input only
        # (diagnostic of the marker effect; the application's verifier is not changed).
        evaluate = verifier._evaluate_pair
        verifier._evaluate_pair = lambda premise, hyp: evaluate(premise, _strip_markers(hyp))
        replayed_nomarker = replay(verifier, rows, premises)
        verifier._evaluate_pair = evaluate
        app = {"false_release": [x["id"] for x in replayed if x["outcome"] == "RELEASE" and x["expected"] == "WITHHOLD"],
               "false_withhold": [x["id"] for x in replayed if x["outcome"] == "WITHHOLD" and x["expected"] == "RELEASE"],
               "released": sum(x["outcome"] == "RELEASE" for x in replayed),
               "expected_release": sum(x["expected"] == "RELEASE" for x in replayed)}
        frozen = [x for x in per_example if x["split"] == "frozen_eval"]
        by_cat = defaultdict(lambda: Counter())
        for x in frozen:
            by_cat[x["category"]]["correct" if x["predicted"] == x["expected_nli_label"] else "wrong"] += 1
        results["models"][name] = {
            "model_id": model_id, "revision": revision,
            "id2label": {str(k): v for k, v in clf.model.config.id2label.items()},
            "setting_a": {"frozen_eval": metrics(frozen, "predicted"),
                          "dev": metrics([x for x in per_example if x["split"] == "dev"], "predicted"),
                          "by_category_frozen": {k: dict(v) for k, v in sorted(by_cat.items())},
                          "median_latency_ms": sorted(x["latency_ms"] for x in per_example)[len(per_example) // 2],
                          "truncated": [x["id"] for x in per_example if x["truncated"]]},
            "setting_b": app,
            "setting_b_marker_stripped": {
                "false_release": [x["id"] for x in replayed_nomarker if x["outcome"] == "RELEASE" and x["expected"] == "WITHHOLD"],
                "false_withhold": [x["id"] for x in replayed_nomarker if x["outcome"] == "WITHHOLD" and x["expected"] == "RELEASE"],
                "released": sum(x["outcome"] == "RELEASE" for x in replayed_nomarker)},
            "per_example": per_example, "replay": replayed,
        }
        print(name, json.dumps({"A_frozen": {k: results["models"][name]["setting_a"]["frozen_eval"][k]
                                             for k in ("accuracy", "macro_f1", "false_acceptance", "false_withholding")},
                                "B": app, "B_marker_stripped": results["models"][name]["setting_b_marker_stripped"]}))
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "NLI_EVAL_RESULTS_V1.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
