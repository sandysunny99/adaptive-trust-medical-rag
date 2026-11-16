"""Round 6: what the pinned RxNorm lexicon recognises, measured (evaluation only; changes nothing).

Reports the lexicon's size, the spans that map to several concepts, how the project's own curated medications
(data/drug_entity_cache.json) are recognised, which drug names the fixed recogniser knows that the lexicon does not,
and the drug-name mentions in the live corpus text. Coverage is reported per name, never as "all drugs".

    uv run python experiments/nli_eval_round6/lexicon_coverage.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_trust_medical_rag.normalization.medication_lexicon import LEXICON_DIR, default_lexicon  # noqa: E402
from adaptive_trust_medical_rag.verification.canonical_identity import _KNOWN_DRUGS  # noqa: E402

OUT = ROOT / "experiments" / "nli_eval_round6" / "results" / "LEXICON_COVERAGE_V1.json"


def main() -> int:
    lex = default_lexicon()
    manifest = json.loads((LEXICON_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    ambiguous = sorted([" ".join(k), sorted(v)] for idx in (lex._exact, lex._folded) for k, v in idx.items() if len(v) > 1)

    cache = json.loads((ROOT / "data" / "drug_entity_cache.json").read_text(encoding="utf-8"))
    curated = []
    for key, entry in cache.items():
        # A brand is looked up as the cache writes it (brand_name), a generic as its key.
        text = entry["brand_name"] if entry.get("brand_name", "").lower() == key else key
        found = [(m.text, m.rxcui, m.tty) for m in lex.mentions(text)]
        curated.append({"name": text, "cache_rxcui": entry.get("rxcui"), "lexicon": found,
                        "recognised_whole": len(found) == 1 and found[0][0] == text,
                        "same_rxcui_as_cache": bool(found) and found[0][1] == entry.get("rxcui")})

    fixed = [n for n in _KNOWN_DRUGS.split("|")]
    fixed_missing = [n for n in fixed if not any(m.text == n for m in lex.mentions(n))]

    corpus = json.loads((ROOT / "data" / "live_medical" / "LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
    corpus_mentions = sorted({m.name or m.text for c in corpus for m in lex.mentions(c["text"])})

    result = {
        "lexicon": {"release": lex.release, "sha256": manifest["lexicon_sha256"], "counts": manifest["counts"],
                    "ambiguous_spans": ambiguous},
        "curated_medications": {
            "total": len(curated),
            "recognised_whole": sum(c["recognised_whole"] for c in curated),
            "same_rxcui_as_cache": sum(c["same_rxcui_as_cache"] for c in curated),
            "rows": curated},
        "fixed_list_names_missing_from_lexicon": fixed_missing,
        "live_corpus_v2_names_recognised": corpus_mentions,
        "note": "Recognition is of RxNorm normalised names in the Current Prescribable Content subset (US prescribable "
                "and many OTC drugs, active only). Synonyms (paracetamol, metamizole), foreign-only, withdrawn and "
                "invented names are not recognised; brand names match only as RxNorm writes them.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result["curated_medications"].items() if k != "rows"}, indent=2))
    print("ambiguous spans:", len(ambiguous), "| fixed-list names missing:", fixed_missing)
    print("not recognised whole:", [(c["name"], c["lexicon"]) for c in curated if not c["recognised_whole"]])
    print("rxcui differs from cache:", [(c["name"], c["cache_rxcui"], c["lexicon"]) for c in curated
                                        if c["recognised_whole"] and not c["same_rxcui_as_cache"]])
    print("corpus names:", corpus_mentions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
