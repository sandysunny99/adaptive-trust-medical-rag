"""Round 5: record what each evaluated NLI model declares about its license, at its exact revision.

Reads only public Hugging Face metadata (no token, no terms accepted, no weights downloaded) and writes
results/MODEL_LICENSE_AUDIT_V1.json. It records declarations; it makes no legal determination. A
declaration seen at one revision is never applied to another.

    uv run python experiments/nli_eval_round5/audit_model_licenses.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parent / "results" / "MODEL_LICENSE_AUDIT_V1.json"
HF = "https://huggingface.co"
MODELS = [  # (role, repository, evaluated revision), as pinned in round 4 and the live verifier
    ("live default", "pritamdeka/PubMedBERT-MNLI-MedNLI", "f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab"),
    ("candidate", "cnut1648/biolinkbert-mednli", "f9f4a9d1e046a0e6574feef938f1308cecaebbd5"),
    ("candidate", "cnut1648/biolinkbert-large-mnli-snli", "89029f481c3c6f49bae0ba0cdb148d9b21847ae6"),
    ("blocked candidate", "ygivenx/modernbert-base-mednli", "7b0ef2489b155f8a53bdd7d56e4ecc9ad9c7b174"),
]
BASES = {  # base models named by each card or its text
    "pritamdeka/PubMedBERT-MNLI-MedNLI": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
    "cnut1648/biolinkbert-mednli": "michiyasunaga/BioLinkBERT-large",
    "cnut1648/biolinkbert-large-mnli-snli": "michiyasunaga/BioLinkBERT-large",
    "ygivenx/modernbert-base-mednli": "answerdotai/ModernBERT-base",
}


def front_matter_license(readme: str) -> str | None:
    m = re.match(r"^---\s*\n(.*?)\n---", readme, re.S)
    lic = re.search(r"^license:\s*(.+)$", m.group(1), re.M) if m else None
    return lic.group(1).strip() if lic else None


def main() -> int:
    out = {"recorded_at": datetime.now(UTC).isoformat(), "method": "public Hugging Face API and README at each revision",
           "note": "Declarations only; no legal determination. Training-data terms are not assessed.", "models": []}
    with httpx.Client(timeout=30, follow_redirects=True) as c:
        for role, repo, rev in MODELS:
            meta = c.get(f"{HF}/api/models/{repo}/revision/{rev}", params={"blobs": "true"}).json()
            readme = c.get(f"{HF}/{repo}/raw/{rev}/README.md")
            files = [s["rfilename"] for s in meta.get("siblings", [])]
            weights = {s["rfilename"]: (s.get("lfs") or {}).get("sha256") for s in meta.get("siblings", [])
                       if s["rfilename"].endswith((".bin", ".safetensors"))}
            history = []
            commits = c.get(f"{HF}/api/models/{repo}/commits/main")
            if not isinstance(commits.json(), list):  # a gated repository needs an authorised account
                history.append({"revision": None, "readme_license":
                                f"history not readable without access (HTTP {commits.status_code})"})
            for commit in commits.json() if isinstance(commits.json(), list) else []:
                r = c.get(f"{HF}/{repo}/raw/{commit['id']}/README.md")
                history.append({"revision": commit["id"], "date": commit["date"][:19], "title": commit["title"],
                                "readme_license": front_matter_license(r.text) if r.status_code == 200 else
                                f"README not readable (HTTP {r.status_code})"})
            base = c.get(f"{HF}/api/models/{BASES[repo]}").json()
            out["models"].append({
                "role": role, "repository": repo, "revision": rev, "resolved_sha": meta.get("sha"),
                "gated": meta.get("gated"), "card_license": (meta.get("cardData") or {}).get("license"),
                "license_tags": [t for t in meta.get("tags", []) if t.startswith("license:")],
                "readme_license_at_revision": front_matter_license(readme.text) if readme.status_code == 200 else
                f"README not readable (HTTP {readme.status_code})",
                "license_files_at_revision": [f for f in files if "license" in f.lower()],
                "weights_sha256": weights, "readme_license_history": history,
                "base_model": {"requested": BASES[repo], "resolves_to": base.get("id"),
                               "current_card_license": (base.get("cardData") or {}).get("license"),
                               "note": "current card; the base revision used for fine-tuning is not recorded"},
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for m in out["models"]:
        declared = [h["revision"][:8] if h["revision"] else h["readme_license"] for h in m["readme_license_history"]
                    if h["readme_license"] is not None and not str(h["readme_license"]).startswith("README not")]
        print(f"{m['repository']}@{m['revision'][:8]}: card={m['card_license']} readme={m['readme_license_at_revision']} "
              f"files={m['license_files_at_revision']} gated={m['gated']} | revisions declaring a license: {declared} "
              f"| base {m['base_model']['resolves_to']}={m['base_model']['current_card_license']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
