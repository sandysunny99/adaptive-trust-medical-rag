"""Round 5: replay the frozen NLI_EVAL_SET_V1 through the full live release policy (evaluation only).

Round 4's setting B swapped classifiers into ClaimVerifierV2 and the source-text bound, but did not
apply the pair-identity check or the rest of the live pipeline. This replay runs every example through
LiveMedicalRAGService.execute() with the pinned live NLI model and all production gates: source
identity, eligibility, trust, the claim verifier with pair identity, the strength checks, the cited-text
bound, the new citation-alignment check and all-or-nothing release. Each example is run twice, with
the alignment check on and off, to show exactly what it changes.

Evidence: the real DailyMed sections the examples were written from (lisinopril 5.5 and 7.1, warfarin
7.3), loaded from the repository's candidate fixtures and approved ONLY inside a temporary folder
with a test-only severity. Production data is not read for approval and not changed. The model is
loaded offline from the local cache at its pinned revision; no text leaves the machine.

The labels are UNREVIEWED (written by an AI assistant); these are engineering results, not clinical
accuracy estimates.

    TESTING= HF_HUB_OFFLINE=1 uv run python experiments/nli_eval_round5/replay_live_policy.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ["HF_HUB_OFFLINE"] = "1"

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate  # noqa: E402
from adaptive_trust_medical_rag.services import live_application, live_relationships  # noqa: E402
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2  # noqa: E402

EVAL = ROOT / "experiments" / "nli_eval_round4" / "NLI_EVAL_SET_V1.jsonl"
OUT = ROOT / "experiments" / "nli_eval_round5" / "results" / "LIVE_POLICY_REPLAY_V1.json"
FIX = ROOT / "tests" / "fixtures"
NAMES = ("LIVE_RELATIONSHIP_RECORDS_V2.json", "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
         "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json")
SEC = {"5.5": "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5", "7.1": "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1",
       "7.3": "DAILYMED-884CDBF6-SPL-V8-SEC-7.3"}
# RxCUIs for every drug an example names (RxNav ingredient concepts); the query names the label's drug
# plus any other listed drug the claim names, as a user asking about that pair would.
RXCUI = {"lisinopril": "29046", "spironolactone": "9997", "warfarin": "11289", "ibuprofen": "5640",
         "aspirin": "1191", "naproxen": "7258", "acetaminophen": "161", "amlodipine": "17767",
         "sertraline": "36437", "amiloride": "644", "triamterene": "10763"}
LABEL_DRUG = {"5.5": "lisinopril", "7.1": "lisinopril", "7.3": "warfarin"}
RELEVANCE = 0.6  # the measured cosine of a real lisinopril section for its query (tests use the same)
# Not part of the frozen set and not labels: round-5 probes of changed facts (a drug, population, severity or
# timing no retrieved section states; P05 is a drug name the application cannot recognise). Diagnostic only.
PROBES = [{"id": f"P0{i}", "section": "5.5", "hypothesis": h} for i, h in enumerate((
    "Enalapril can cause hyperkalemia in patients with renal insufficiency.",
    "Lisinopril can cause hyperkalemia in pediatric patients with renal insufficiency.",
    "Lisinopril causes fatal hyperkalemia in patients with renal insufficiency.",
    "Lisinopril causes hyperkalemia within 24 hours in patients with renal insufficiency.",
    "Furosemide can cause hyperkalemia in patients with renal insufficiency."), start=1)]
PROBES.append({"id": "P06", "section": "7.1", "hypothesis": PROBES[-1]["hypothesis"]})  # P05 cited to 7.1


def put(root: Path, folder: str, fixture: str) -> None:
    dest = root / "v2" / folder
    dest.mkdir(parents=True)
    records = json.loads((FIX / fixture / NAMES[0]).read_text(encoding="utf-8"))
    for r in records["records"]:
        r["severity"] = "MODERATE"  # test-only grade so the record loads; not a clinical grade
    rec_raw = (json.dumps(records) + "\n").encode()
    ev_raw = (FIX / fixture / NAMES[1]).read_bytes().replace(b"\r\n", b"\n")
    (dest / NAMES[0]).write_bytes(rec_raw)
    (dest / NAMES[1]).write_bytes(ev_raw)
    manifest = json.loads((FIX / fixture / NAMES[2]).read_text(encoding="utf-8"))
    assert manifest["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL"
    manifest.update(status="APPROVED", approval={"approved_by": "TEST-ONLY replay", "approved_at": "2026-10-26"},
                    records_sha256=hashlib.sha256(rec_raw).hexdigest(), evidence_sha256=hashlib.sha256(ev_raw).hexdigest())
    (dest / NAMES[2]).write_text(json.dumps(manifest), encoding="utf-8")


def load_state(tmp: Path) -> SimpleNamespace:
    for folder, fixture in (("a_food_0001", "food_0001_candidate"), ("b_rel_live_0003", "rel_live_0003_candidate"),
                            ("c_rel_live_0004", "rel_live_0004_candidate")):
        put(tmp, folder, fixture)
    for name in ("LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json", "LIVE_RELATIONSHIP_RECORDS_V1.json"):
        shutil.copyfile(ROOT / "data" / "live_medical" / "relationships" / name, tmp / name)
    live_relationships.RELATIONSHIP_DIR = str(tmp)
    os.environ["TESTING"] = "1"  # stub embeddings for the load only; the verifier below is the real model
    state = SimpleNamespace(claim_verifier=object(), model_init_errors={})
    live_application._lazy_init_models(state)
    del os.environ["TESTING"]
    return state


def candidate(item: dict) -> ScoredCandidate:
    return ScoredCandidate(Candidate(
        chunk_id=item["chunk_id"], document_id=item["document_id"], text=item["text"],
        source_url=item["document_url"], source_authority=item.get("authority", 0.5),
        metadata={"provenance": item.get("provenance", {}), "source_type": item.get("source_type"),
                  "freshness_score": item.get("freshness", 0.8), "source_identity": item.get("source_identity"),
                  "supported_claims": item.get("supported_claims")}), vector_similarity=RELEVANCE)


class Normalizer:
    async def normalize_batch(self, names):
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI[n.lower()], brand_name=None,
                                formulation=None, confidence=1.0, source="TEST") for n in names]


class Retrieval:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query, query_drugs, top_k=20):
        return self.chunks


class LLM:
    def __init__(self, conclusion):
        self.content = json.dumps({"conclusion": conclusion})

    async def generate_structured(self, prompt, response_format, provider_name=None):
        return SimpleNamespace(content=self.content, provider="replay", model="replay")


def replay(example: dict, loaded: SimpleNamespace, verifier) -> dict:
    section = example["section"]
    by_id = {e["chunk_id"]: e for e in loaded.relationship_store.evidence}
    # Every retrieved section of the label, as the live app would retrieve them; the claim cites its own.
    retrieved = [SEC["5.5"], SEC["7.1"]] if section in ("5.5", "7.1") else [SEC["7.3"]]
    cite = retrieved.index(SEC[section]) + 1
    named = [d for d in RXCUI if re.search(rf"\b{d}\b", example["hypothesis"], re.I) and d != LABEL_DRUG[section]]
    drugs = [LABEL_DRUG[section].capitalize()] + [d.capitalize() for d in named]
    state = SimpleNamespace(
        drug_normalizer=Normalizer(), retrieval_engine=Retrieval([candidate(by_id[c]) for c in retrieved]),
        llm_backend=LLM(f"{example['hypothesis'].rstrip('.')} [Source {cite}]."), claim_verifier=verifier,
        model_init_errors={}, relationship_store=loaded.relationship_store,
        shared_source_urls=loaded.shared_source_urls, verified_source_links=loaded.verified_source_links)

    async def collect():
        return [e async for e in live_application.LiveMedicalRAGService(state).execute(
            f"replay-{example['id']}", drugs, None, 0)]

    events = asyncio.run(collect())
    (kind, data) = next((e["event"], e["data"]) for e in events if e["event"] in ("answer", "abstention", "error"))
    claim = (data.get("claims") or [{}])[0]
    # NLI of the statement the verifier scored (with its [Source N] marker) against each retrieved section,
    # recomputed for the record. Only the cited chunk can support it (the verifier's cited-chunk gate);
    # uncited rows are diagnostic only.
    chunks = []
    for n, c in enumerate(retrieved, start=1):
        scores = {lbl: round(v, 4) for lbl, v in verifier._evaluate_pair(by_id[c]["text"], claim["text"]).items()}
        chunks.append({"source": f"Source {n}", "chunk_id": c, "section": next(k for k, v in SEC.items() if v == c),
                       "role": "cited (supporting candidate)" if n == cite else "uncited (diagnostic only)",
                       "nli": scores, "nli_verdict": max(scores, key=scores.get)})
    return {"outcome": "RELEASE" if kind == "answer" else "WITHHOLD", "terminal": kind, "drugs": drugs,
            "claim": claim.get("text"), "citation_marker": f"[Source {cite}]", "cited_chunk": SEC[section],
            "cited_document": by_id[SEC[section]]["document_id"], "chunks": chunks,
            "support_state": claim.get("support_state"), "verifier_decision": claim.get("verifier_decision"),
            "citation_supports_claim": claim.get("citation_supports_claim"),
            "entailment": claim.get("entailment"), "entailment_chunk_id": claim.get("entailment_chunk_id"),
            "canonical_identity_status": claim.get("canonical_identity_status"),
            "strength_check": claim.get("strength_check"), "citation_alignment": claim.get("citation_alignment"),
            "medication_identity": claim.get("medication_identity"), "withheld_by": withheld_by(kind, claim), "reason": (data.get("reason") or "")[:240]}


def withheld_by(kind: str, claim: dict) -> list[str]:
    """Every gate that set this claim against release, in pipeline order (empty when released)."""
    if kind == "answer":
        return []
    gates = []
    if claim.get("invalid_source_references") or not claim.get("citation_present"):
        gates.append("citation missing or invalid")
    if claim.get("citation_present") and not claim.get("citation_supports_claim"):
        gates.append("verifier: cited chunk does not entail")
    elif claim.get("canonical_identity_status") not in (None, "MATCH"):
        gates.append(f"verifier: pair identity {claim['canonical_identity_status']}")
    elif claim.get("verifier_decision") != "release" or (
            claim.get("support_state") != "SUPPORTED"
            and not any(claim.get(k) for k in ("strength_check", "citation_alignment", "medication_identity"))):
        gates.append(f"verifier: aggregate state {claim.get('support_state')} over all retrieved chunks")
    if claim.get("strength_check"):
        gates.append("strength / source-text check")
    if claim.get("citation_alignment"):
        gates.append("citation alignment screen")
    if claim.get("medication_identity"):
        gates.append("medication identity guard")
    return gates or ["after claim verification (trust or release gate); see reason"]


def main() -> int:
    examples = [json.loads(line) for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()]
    verifier = ClaimVerifierV2()  # the live default: PubMedBERT-MNLI-MedNLI at its pinned revision
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        loaded = load_state(Path(tmp))
        real_check = live_application.citation_alignment_violation
        for ex in examples:
            with_check = replay(ex, loaded, verifier)
            live_application.citation_alignment_violation = lambda *a, **k: None
            try:
                without = replay(ex, loaded, verifier)
            finally:
                live_application.citation_alignment_violation = real_check
            rows.append({"id": ex["id"], "split": ex["split"], "category": ex["category"],
                         "expected_app_outcome": ex["expected_app_outcome"], "with_alignment": with_check,
                         "without_alignment": without})
        probes = [{"id": pr["id"], "result": replay(pr, loaded, verifier)} for pr in PROBES]

    def tally(key):
        rel = [r for r in rows if r[key]["outcome"] == "RELEASE"]
        return {"released": len(rel),
                "false_releases": [r["id"] for r in rel if r["expected_app_outcome"] != "RELEASE"],
                "false_withholds": [r["id"] for r in rows
                                    if r["expected_app_outcome"] == "RELEASE" and r[key]["outcome"] != "RELEASE"]}

    summary = {"with_alignment": tally("with_alignment"), "without_alignment": tally("without_alignment"),
               "changed_by_alignment": [r["id"] for r in rows
                                        if r["with_alignment"]["outcome"] != r["without_alignment"]["outcome"]]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"dataset": "NLI_EVAL_SET_V1", "dataset_sha256": hashlib.sha256(EVAL.read_bytes()).hexdigest(),
                               "model": f"{verifier.model_id}@{verifier.revision}", "labels": "UNREVIEWED",
                               "summary": summary, "examples": rows,
                               "probes_note": "diagnostic probes, not part of NLI_EVAL_SET_V1 and not labels",
                               "probes": probes}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    for pr in probes:
        print(pr["id"], pr["result"]["outcome"], pr["result"]["withheld_by"], pr["result"]["chunks"][0]["nli"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
