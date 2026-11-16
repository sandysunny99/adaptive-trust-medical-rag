"""Dry run of the pending REL-LIVE-0002 candidate (revision 2) through the V2 loading path.

Nothing here approves the candidate. The candidate files are only read. An "approved" copy is
written to a temporary directory outside the repository, labelled DRY-RUN, used, and deleted.
Runs with real models (TESTING must be unset): all-MiniLM-L6-v2 retrieval over the frozen corpus
plus any loaded V2 evidence, and ClaimVerifierV2 with its real NLI model. The normalizer and the
LLM are stubs: the LLM returns a fixed one-sentence answer so the verifier's decision is the
only thing under test.
Usage: python dryrun_v2_candidate.py <repo_root> <candidate_dir>
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

repo, cand = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / "src"))
assert os.environ.get("TESTING") != "1", "run with real models"
from adaptive_trust_medical_rag.services import live_relationships  # noqa: E402
from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService, _lazy_init_models  # noqa: E402
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2  # noqa: E402

corpus = json.loads((repo / "data/live_medical/LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
RXCUI = {"simvastatin": "36567", "clarithromycin": "21212", "metformin": "6809"}
VERIFIER = ClaimVerifierV2()


class Normalizer:
    async def normalize_batch(self, names):
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI[n.lower()], brand_name=None,
                                formulation=None, confidence=1.0, source="DRY-RUN") for n in names]


class FixedLLM:
    def __init__(self, text):
        self.content = json.dumps({"conclusion": text})

    async def generate_structured(self, prompt, response_format, provider_name=None):
        return SimpleNamespace(content=self.content, provider="dry-run", model="fixed-answer")


def run(label, directory, claim, drugs=("Simvastatin", "Clarithromycin")):
    live_relationships.RELATIONSHIP_DIR = str(directory)
    state = SimpleNamespace(claim_verifier=VERIFIER, model_init_errors={})
    _lazy_init_models(state)
    state.drug_normalizer, state.llm_backend = Normalizer(), FixedLLM(claim)

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(f"dry-{label}", list(drugs), None, 0)]

    events = asyncio.run(collect())
    get = lambda name: next((e["data"] for e in events if e["event"] == name), None)  # noqa: E731
    term = next(e for e in events if e["event"] in ("answer", "abstention", "error"))
    retrieval, trust = get("retrieval"), get("trust")
    claims = [(c.get("support_state"), c.get("canonical_identity_status"), round(c.get("entailment") or 0, 3))
              for c in term["data"].get("claims", [])]
    print(json.dumps({
        "case": label, "store": state.relationship_store.reason,
        "retrieval": {k: retrieval.get(k) for k in ("evidence_count", "embedding_mode", "relationship_evidence_chunks")} if retrieval else None,
        "trust": {k: trust.get(k) for k in ("risk_class", "threshold", "risk_basis", "is_eligible", "unrelated_excluded")} if trust else None,
        "eligible_evidence": [e["chunk_id"] for e in term["data"].get("evidence", [])],
        "claim": claim, "claims": claims,
        "terminal": term["event"], "reason": term["data"].get("reason") or term["data"].get("message"),
    }, indent=1, ensure_ascii=False))


tmp = Path(tempfile.mkdtemp(prefix="v2-dryrun-"))
try:
    approved, tampered = tmp / "approved", tmp / "tampered"
    for d in (approved, tampered):
        shutil.copytree(cand, d)
        m = json.loads((d / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
        m.update(status="APPROVED", approval={"approved_by": "DRY-RUN copy, not an approval", "approved_at": "DRY-RUN"})
        (d / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(json.dumps(m), encoding="utf-8")
    ev = tampered / "LIVE_RELATIONSHIP_EVIDENCE_V2.json"
    ev.write_bytes(ev.read_bytes().replace(b"is contraindicated", b"is acceptable"))

    good = "Simvastatin with clarithromycin is contraindicated [Source 1]."
    run("pending-as-is", cand, good)
    run("approved-copy", approved, good)
    run("approved-copy-reversed-order", approved, "Clarithromycin with simvastatin is contraindicated [Source 1].")
    run("approved-copy-wrong-predicate", approved, "Simvastatin inhibits clarithromycin [Source 1].")
    run("approved-copy-unsupported-detail", approved, "Simvastatin with clarithromycin causes liver failure [Source 1].")
    run("approved-copy-tampered-evidence", tampered, good)
finally:
    shutil.rmtree(tmp)
    print(f"temporary directory removed: {not tmp.exists()}")
